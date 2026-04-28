import torch
import numpy as np
import cv2

class WatermarkEngine:
    """
    Robust algorithmic DCT-based watermarking engine.
    Drop-in replacement for the CNN autoencoder engine.
    """
    def __init__(self, payload_size=32, device=None, alpha=8.0):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
            
        self.payload_size = payload_size
        self.alpha = float(alpha)  # Strength of watermark
        
        # Two mid-frequency DCT coordinates to compare
        self.p1 = (5, 5)
        self.p2 = (4, 4)
        
        print(f"[Watermark Engine] Initialized Robust DCT Engine (payload size: {payload_size})")

    @torch.no_grad()
    def generate_random_payload(self):
        # Generate a random binary vector, same shape as DL model returned: (1, payload_size)
        return torch.randint(0, 2, (1, self.payload_size), dtype=torch.float32).to(self.device)

    def _embed_dct_numpy(self, img_np, payload_bits):
        """
        img_np: numpy array (H, W, 3) in RGB, values [0, 255]
        payload_bits: list or 1D arrays of 0s and 1s
        """
        # Convert to YCrCb
        img_yuv = cv2.cvtColor(img_np, cv2.COLOR_RGB2YCrCb)
        Y = img_yuv[:,:,0].astype(np.float32)
        
        H, W = Y.shape
        # Pad if necessary so dimensions are multiples of 8
        pad_h = (8 - H % 8) % 8
        pad_w = (8 - W % 8) % 8
        
        if pad_h > 0 or pad_w > 0:
            Y = np.pad(Y, ((0, pad_h), (0, pad_w)), mode='reflect')
            
        new_H, new_W = Y.shape
        
        # We will cycle through the payload bits to embed them redundantly across the whole image
        bit_idx = 0
        
        for i in range(0, new_H, 8):
            for j in range(0, new_W, 8):
                block = Y[i:i+8, j:j+8]
                dct_block = cv2.dct(block)
                
                bit = payload_bits[bit_idx % self.payload_size]
                
                val1 = dct_block[self.p1]
                val2 = dct_block[self.p2]
                
                # We want val1 > val2 if bit == 1, else val1 < val2 if bit == 0
                diff = val1 - val2
                
                if bit == 1:
                    if diff < self.alpha:
                        dct_block[self.p1] += (self.alpha - diff) / 2.0
                        dct_block[self.p2] -= (self.alpha - diff) / 2.0
                else:
                    if diff > -self.alpha:
                        dct_block[self.p1] -= (diff + self.alpha) / 2.0
                        dct_block[self.p2] += (diff + self.alpha) / 2.0
                        
                idct_block = cv2.idct(dct_block)
                Y[i:i+8, j:j+8] = idct_block
                
                bit_idx += 1
                
        # Remove padding
        if pad_h > 0 or pad_w > 0:
            Y = Y[:H, :W]
            
        img_yuv[:,:,0] = np.clip(np.round(Y), 0, 255).astype(np.uint8)
        # Convert back
        watermarked_rgb = cv2.cvtColor(img_yuv, cv2.COLOR_YCrCb2RGB)
        return watermarked_rgb

    def _extract_dct_numpy(self, img_np):
        """
        img_np: numpy array (H, W, 3) in RGB, values [0, 255]
        """
        img_yuv = cv2.cvtColor(img_np, cv2.COLOR_RGB2YCrCb)
        Y = img_yuv[:,:,0].astype(np.float32)
        
        H, W = Y.shape
        pad_h = (8 - H % 8) % 8
        pad_w = (8 - W % 8) % 8
        
        if pad_h > 0 or pad_w > 0:
            Y = np.pad(Y, ((0, pad_h), (0, pad_w)), mode='reflect')
            
        new_H, new_W = Y.shape
        
        scores = np.zeros(self.payload_size)
        counts = np.zeros(self.payload_size)
        
        bit_idx = 0
        for i in range(0, new_H, 8):
            for j in range(0, new_W, 8):
                block = Y[i:i+8, j:j+8]
                dct_block = cv2.dct(block)
                
                val1 = dct_block[self.p1]
                val2 = dct_block[self.p2]
                
                payload_idx = bit_idx % self.payload_size
                
                if val1 > val2:
                    scores[payload_idx] += 1
                counts[payload_idx] += 1
                
                bit_idx += 1
                
        extracted_bits = (scores > (counts / 2.0)).astype(np.float32)
        return extracted_bits

    @torch.no_grad()
    def embed_watermark(self, image_tensor, payload):
        """
        image_tensor: (1, 3, H, W) normalized to [0, 1]
        payload: (1, payload_size) binary
        returns watermarked_tensor
        """
        # Convert to numpy
        img_np = (image_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        payload_bits = payload.squeeze(0).cpu().numpy()
        
        watermarked_np = self._embed_dct_numpy(img_np, payload_bits)
        
        # Convert back to tensor
        watermarked_tensor = torch.from_numpy(watermarked_np).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        return watermarked_tensor.to(self.device).clamp(0.0, 1.0)
        
    @torch.no_grad()
    def extract_watermark(self, image_tensor):
        """
        image_tensor: (1, 3, H, W) normalized to [0, 1]
        returns predicted payload (1, payload_size)
        """
        img_np = (image_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        extracted_bits = self._extract_dct_numpy(img_np)
        return torch.from_numpy(extracted_bits).view(1, self.payload_size).to(self.device)
        
    def process_image(self, input_path, output_path, payload):
        from PIL import Image
        import torchvision.transforms.functional as TF
        img = Image.open(input_path).convert("RGB")
        tensor = TF.to_tensor(img).unsqueeze(0).to(self.device)
        watermarked = self.embed_watermark(tensor, payload)
        
        watermarked_img = TF.to_pil_image(watermarked.squeeze(0).cpu())
        watermarked_img.save(output_path, quality=95)
        
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
                
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            tensor = TF.to_tensor(rgb).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                watermarked = self.embed_watermark(tensor, payload)
            
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
    np.random.seed(42)
    engine = WatermarkEngine()
    dummy_img = torch.rand(1, 3, 224, 224).to(engine.device)
    payload = engine.generate_random_payload()
    
    watermarked = engine.embed_watermark(dummy_img, payload)
    extracted = engine.extract_watermark(watermarked)
    
    print("Original:", payload[0][:8].int().tolist())
    print("Extracted:", extracted[0][:8].int().tolist())
    
    # Test JPEG Robustness
    img_np = (watermarked.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
    ret, jpeg_buf = cv2.imencode('.jpg', cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR), [int(cv2.IMWRITE_JPEG_QUALITY), 60])
    jpeg_img = cv2.imdecode(jpeg_buf, 1)
    jpeg_rgb = cv2.cvtColor(jpeg_img, cv2.COLOR_BGR2RGB)
    
    jpeg_tensor = torch.from_numpy(jpeg_rgb).permute(2, 0, 1).unsqueeze(0).float() / 255.0
    jpeg_extracted = engine.extract_watermark(jpeg_tensor.to(engine.device))
    
    print("After JPEG 60:", jpeg_extracted[0][:8].int().tolist())
    print("Matches Original:", (payload == jpeg_extracted).float().mean().item() == 1.0)
