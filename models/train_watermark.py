import os
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
import numpy as np

# Import the existing models
from watermark_2d import Encoder2D, Decoder2D

class NoiseLayer(nn.Module):
    """
    A Differentiable layer simulating JPEG/MP4 compression artifacts 
    and general noise for robustness training.
    """
    def __init__(self, std=0.02):
        super().__init__()
        self.std = std

    def forward(self, x):
        # 1. Skip Gaussian noise as it overrides the small alpha=0.05 signal
        x_noisy = x

        # 2. Differentiable Quantization (Simulating 8-bit quantization and compression loss)
        # Using Straight-Through Estimator (STE)
        x_scaled = x_noisy * 255.0
        x_quantized = torch.round(x_scaled)
        # STE trick:
        x_quantized = x_scaled + (x_quantized - x_scaled).detach()
        x_quantized = x_quantized / 255.0
        
        return torch.clamp(x_quantized, 0.0, 1.0)


class DummyDataset(Dataset):
    """
    Generates dummy images and binary payloads for training the AutoEncoder
    """
    def __init__(self, num_samples, img_size=(224, 224), payload_size=32):
        self.num_samples = num_samples
        self.img_size = img_size
        self.payload_size = payload_size

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        # Random natural-looking images (just random noise blurred or low frequency for dummy training)
        # Using flat random colors makes it MUCH easier for the PoC network to learn the watermark pattern
        # Keep values between 0.2 and 0.8 to avoid torch.clamp killing gradients in the encoder
        img = torch.ones(3, *self.img_size) * (torch.rand(3, 1, 1) * 0.6 + 0.2)
        payload = torch.randint(0, 2, (self.payload_size,), dtype=torch.float32)
        return img, payload

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Hyperparameters
    payload_size = 32
    batch_size = 16
    num_epochs = 30
    num_samples_per_epoch = 800
    learning_rate = 1e-4

    # Instantiate models
    encoder = Encoder2D(payload_size=payload_size).to(device)
    decoder = Decoder2D(payload_size=payload_size).to(device)
    noise_layer = NoiseLayer(std=0.03).to(device)

    optimizer = optim.Adam(list(encoder.parameters()) + list(decoder.parameters()), lr=learning_rate)
    
    # Loss functions
    mse_loss_fn = nn.MSELoss()
    bce_loss_fn = nn.BCELoss()

    # Dataset
    dataset = DummyDataset(num_samples=num_samples_per_epoch, payload_size=payload_size)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    print("Starting training...")
    for epoch in range(num_epochs):
        encoder.train()
        decoder.train()
        
        total_loss = 0
        total_img_loss = 0
        total_payload_loss = 0
        correct_bits = 0
        total_bits = 0

        for images, payloads in dataloader:
            images = images.to(device)
            payloads = payloads.to(device)
            
            optimizer.zero_grad()
            
            # Embed watermark
            watermarked_images = encoder(images, payloads)
            
            # Apply differentiable noise
            noisy_images = noise_layer(watermarked_images)
            
            # Extract watermark from noisy images
            extracted_payloads = decoder(noisy_images)
            
            # Compute losses
            # We want the watermarked image to be imperceptible (close to original)
            img_loss = mse_loss_fn(watermarked_images, images)
            
            # We want the extracted payload to exactly match the embedded payload
            payload_loss = bce_loss_fn(extracted_payloads, payloads)
            if epoch == 0 and total_bits == 0:
                print(f"Step 0 payload_loss: {payload_loss.item()}")
            
            # Weighted sum of losses
            # Give payload loss massive priority so it actually embeds something!
            loss = 1.0 * img_loss + 20.0 * payload_loss
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            total_img_loss += img_loss.item()
            total_payload_loss += payload_loss.item()
            
            # Calculate accuracy
            predicted_bits = torch.round(extracted_payloads)
            correct_bits += (predicted_bits == payloads).sum().item()
            total_bits += payloads.numel()
            
        avg_loss = total_loss / len(dataloader)
        avg_img_loss = total_img_loss / len(dataloader)
        avg_payload_loss = total_payload_loss / len(dataloader)
        accuracy = correct_bits / total_bits
        
        print(f"Epoch [{epoch+1}/{num_epochs}] | "
              f"Loss: {avg_loss:.4f} (Img: {avg_img_loss:.4f}, Payload: {avg_payload_loss:.4f}) | "
              f"Bit Accuracy: {accuracy*100:.2f}%")

    # Save weights
    base_dir = os.path.dirname(os.path.abspath(__file__))
    weights_dir = os.path.join(base_dir, "weights")
    os.makedirs(weights_dir, exist_ok=True)
    
    enc_path = os.path.join(weights_dir, "encoder.pth")
    dec_path = os.path.join(weights_dir, "decoder.pth")
    
    torch.save(encoder.state_dict(), enc_path)
    torch.save(decoder.state_dict(), dec_path)
    print(f"Models saved to {weights_dir}")

if __name__ == "__main__":
    train()
