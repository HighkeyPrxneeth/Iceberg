import torch
from models.watermark_2d import Encoder2D, Decoder2D
import torch.nn as nn

enc = Encoder2D()
dec = Decoder2D()
img = torch.ones(1, 3, 224, 224) * 0.5
payload = torch.randint(0, 2, (1, 32)).float()

w_img = enc(img, payload)
pred = dec(w_img)

print("w_img.shape", w_img.shape)
print("pred.shape", pred.shape)
print("payload.shape", payload.shape)

loss = nn.BCELoss()(pred, payload)
print("BCE Loss:", loss.item())
loss.backward()

print("Encoder payload_proj.weight.grad sum:", enc.payload_proj.weight.grad.sum().item() if enc.payload_proj.weight.grad is not None else "None")
print("Encoder conv3.weight.grad sum:", enc.conv3.weight.grad.sum().item() if enc.conv3.weight.grad is not None else "None")
print("Decoder fc.weight.grad sum:", dec.fc.weight.grad.sum().item() if dec.fc.weight.grad is not None else "None")
