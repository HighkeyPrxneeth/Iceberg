import torch
import torch.nn as nn
import torch.nn.functional as F

class Encoder2D(nn.Module):
    """
    Lightweight 2D CNN Encoder to embed a binary payload into video frames.
    """
    def __init__(self, payload_size=32):
        super().__init__()
        self.payload_size = payload_size
        
        # We project the payload into a spatial feature map
        self.payload_proj = nn.Linear(payload_size, 32 * 32)
        
        # We concatenate the 3 channel image with the 1 channel payload map
        self.conv1 = nn.Conv2d(4, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 32, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(32, 3, kernel_size=3, padding=1)
        
        # Scaling factor is 0.05 to keep watermark imperceptible
        self.alpha = 0.05

    def forward(self, image, payload):
        # image: (B, 3, H, W)
        # payload: (B, payload_size)
        B, C, H, W = image.shape
        
        # Expand payload to (B, 1, H, W)
        p = self.payload_proj(payload) # (B, 1024)
        p = p.view(B, 1, 32, 32)
        p = F.interpolate(p, size=(H, W), mode='bilinear', align_corners=False)
        
        x = torch.cat([image, p], dim=1)
        
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        watermark = torch.tanh(self.conv3(x))
        
        # Residual connection
        watermarked_image = image + self.alpha * watermark
        return torch.clamp(watermarked_image, 0.0, 1.0)


class Decoder2D(nn.Module):
    """
    Lightweight 2D CNN Decoder to extract a binary payload from video frames.
    """
    def __init__(self, payload_size=32):
        super().__init__()
        self.payload_size = payload_size
        
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        
        # Adaptive pooling ensures any input spatial dimension resolves to 14x14
        self.pool = nn.AdaptiveAvgPool2d((14, 14))
        
        # 224 / 16 = 14. Flattening preserves spatial watermark patterns better than global average pooling.
        self.flatten = nn.Flatten()
        self.fc = nn.Linear(256 * 14 * 14, payload_size)

    def forward(self, image):
        # image: (B, 3, H, W)
        x = F.relu(self.bn1(self.conv1(image)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = F.relu(self.bn3(self.conv3(x)))
        x = F.relu(self.bn4(self.conv4(x)))
        
        x = self.pool(x)
        x = self.flatten(x)
        payload_pred = torch.sigmoid(self.fc(x))
        return payload_pred

class WatermarkEngine:
    """
    A high-level interface to handle watermarking of frames/videos.
    """
    def __init__(self, payload_size=32, device=None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
            
        self.payload_size = payload_size
        self.encoder = Encoder2D(payload_size).to(self.device)
        self.decoder = Decoder2D(payload_size).to(self.device)
        
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        enc_path = os.path.join(base_dir, "weights", "encoder.pth")
        dec_path = os.path.join(base_dir, "weights", "decoder.pth")
        
        if os.path.exists(enc_path) and os.path.exists(dec_path):
            # weights_only=True for safe loading
            self.encoder.load_state_dict(torch.load(enc_path, map_location=self.device, weights_only=True))
            self.decoder.load_state_dict(torch.load(dec_path, map_location=self.device, weights_only=True))
            print("[Watermark Engine] Loaded trained weights from models/weights/")
        else:
            print("[Watermark Engine] No trained weights found. Using random initialization.")
            
        self.encoder.eval()
        self.decoder.eval()
        
        print(f"[Watermark Engine] Initialized on {self.device} (payload size: {payload_size})")

    @torch.no_grad()
    def generate_random_payload(self):
        # Generate a random binary vector
        return torch.randint(0, 2, (1, self.payload_size), dtype=torch.float32).to(self.device)
        
    @torch.no_grad()
    def embed_watermark(self, image_tensor, payload):
        """
        image_tensor: (1, 3, H, W) normalized to [0, 1]
        payload: (1, payload_size) binary
        returns watermarked_tensor
        """
        # Since it's untrained, it just lightly noise-injects the image
        return self.encoder(image_tensor, payload)
        
    @torch.no_grad()
    def extract_watermark(self, image_tensor):
        """
        image_tensor: (1, 3, H, W) normalized to [0, 1]
        returns predicted payload (1, payload_size)
        """
        return self.decoder(image_tensor)
        
    def process_image(self, input_path, output_path, payload):
        from PIL import Image
        import torchvision.transforms.functional as TF
        img = Image.open(input_path).convert("RGB")
        tensor = TF.to_tensor(img).unsqueeze(0).to(self.device)
        watermarked = self.embed_watermark(tensor, payload)
        
        # Save back
        watermarked_img = TF.to_pil_image(watermarked.squeeze(0).cpu())
        watermarked_img.save(output_path)
        
    def process_video(self, input_path, output_path, payload, progress_cb=None):
        import cv2
        import torchvision.transforms.functional as TF
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            print(f"[Watermark Engine] Failed to open {input_path}")
            return
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert BGR to RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            tensor = TF.to_tensor(rgb).unsqueeze(0).to(self.device)
            
            # Embed
            with torch.no_grad():
                watermarked = self.embed_watermark(tensor, payload)
            
            # Convert back to BGR
            watermarked_np = (watermarked.squeeze(0).cpu().numpy().transpose(1, 2, 0) * 255).astype('uint8')
            bgr = cv2.cvtColor(watermarked_np, cv2.COLOR_RGB2BGR)
            
            out.write(bgr)
            
            frame_idx += 1
            if progress_cb and frame_idx % 5 == 0:
                progress_cb(frame_idx, total_frames)
                
        cap.release()
        out.release()
        if progress_cb:
            progress_cb(total_frames, total_frames)

if __name__ == "__main__":
    engine = WatermarkEngine()
    dummy_img = torch.rand(1, 3, 224, 224).to(engine.device)
    payload = engine.generate_random_payload()
    
    watermarked = engine.embed_watermark(dummy_img, payload)
    extracted = engine.extract_watermark(watermarked)
    
    print("Original Payload:", payload[0][:5], "...")
    print("Extracted Payload:", extracted[0][:5], "...")
    print("Image difference MSE:", F.mse_loss(dummy_img, watermarked).item())
