"""
LSTM-based Velocity Anomaly Detector
=====================================
Trains on synthetic URL-share velocity time series to classify
normal vs. anomalous (piracy-spike) propagation patterns.
Runs on CUDA if available.
"""

import torch
import torch.nn as nn
import numpy as np
import os
import time


class VelocityLSTM(nn.Module):
    """
    Sequence-to-one LSTM classifier.
    Input:  (batch, seq_len, 1)  — velocity values over time
    Output: (batch, 1)           — anomaly probability [0..1]
    """

    def __init__(self, input_size=1, hidden_size=64, num_layers=2, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout,
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        # x: (batch, seq_len, 1)
        lstm_out, _ = self.lstm(x)
        # Take the last hidden state
        last_hidden = lstm_out[:, -1, :]
        return self.classifier(last_hidden)


# ---------------------------------------------------------------------------
# Synthetic data generation
# ---------------------------------------------------------------------------

def generate_normal_series(seq_len=60, batch_size=1):
    """
    Normal traffic: low steady velocity with small Gaussian noise.
    Shares-per-minute hovers between 1-15.
    """
    base = np.random.uniform(2, 10, size=(batch_size, 1))
    noise = np.random.normal(0, 1.5, size=(batch_size, seq_len))
    series = base + noise
    series = np.clip(series, 0, 20)
    return series.astype(np.float32)


def generate_anomaly_series(seq_len=60, batch_size=1):
    """
    Anomalous traffic: starts normal, then explodes exponentially
    in the last 30-50% of the window (simulating a piracy spike).
    """
    series = np.zeros((batch_size, seq_len), dtype=np.float32)
    for i in range(batch_size):
        # Normal preamble
        split = np.random.randint(seq_len // 3, int(seq_len * 0.6))
        base = np.random.uniform(2, 8)
        series[i, :split] = base + np.random.normal(0, 1.2, size=split)

        # Exponential spike
        spike_len = seq_len - split
        t = np.linspace(0, 4, spike_len)
        spike_magnitude = np.random.uniform(30, 120)
        series[i, split:] = base + spike_magnitude * (np.exp(t) / np.exp(4))

        # Add noise over the spike
        series[i, split:] += np.random.normal(0, 2.0, size=spike_len)

    series = np.clip(series, 0, 500)
    return series


def generate_training_batch(batch_size=64, seq_len=60):
    """Generate a balanced batch of normal and anomalous sequences."""
    half = batch_size // 2
    normal = generate_normal_series(seq_len, half)
    anomaly = generate_anomaly_series(seq_len, half)

    data = np.concatenate([normal, anomaly], axis=0)
    labels = np.concatenate([
        np.zeros(half, dtype=np.float32),
        np.ones(half, dtype=np.float32),
    ])

    # Shuffle
    indices = np.random.permutation(batch_size)
    data = data[indices]
    labels = labels[indices]

    # Convert to tensors: (batch, seq_len, 1)
    data_tensor = torch.from_numpy(data).unsqueeze(-1)
    label_tensor = torch.from_numpy(labels).unsqueeze(-1)
    return data_tensor, label_tensor


# ---------------------------------------------------------------------------
# Training harness
# ---------------------------------------------------------------------------

def train_lstm(
    save_dir="data",
    epochs=50,
    batch_size=128,
    lr=1e-3,
    seq_len=60,
    batches_per_epoch=40,
):
    """
    Train the LSTM anomaly detector on synthetic velocity data.
    Saves trained weights to save_dir/lstm_detector.pt.
    Returns the trained model.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[LSTM] Training on device: {device}")

    model = VelocityLSTM().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    os.makedirs(save_dir, exist_ok=True)
    best_loss = float("inf")

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss = 0.0
        correct = 0
        total = 0

        for _ in range(batches_per_epoch):
            data, labels = generate_training_batch(batch_size, seq_len)
            data, labels = data.to(device), labels.to(device)

            optimizer.zero_grad()
            preds = model(data)
            loss = criterion(preds, labels)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            predicted = (preds > 0.5).float()
            correct += (predicted == labels).sum().item()
            total += labels.size(0)

        scheduler.step()
        avg_loss = epoch_loss / batches_per_epoch
        accuracy = correct / total * 100

        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(model.state_dict(), os.path.join(save_dir, "lstm_detector.pt"))

        if epoch % 5 == 0 or epoch == 1:
            print(
                f"[LSTM] Epoch {epoch:3d}/{epochs} | "
                f"Loss: {avg_loss:.4f} | Acc: {accuracy:.1f}% | "
                f"LR: {scheduler.get_last_lr()[0]:.6f}"
            )

    print(f"[LSTM] Training complete. Best loss: {best_loss:.4f}")
    print(f"[LSTM] Model saved to {os.path.join(save_dir, 'lstm_detector.pt')}")
    return model


def load_lstm(save_dir="data", device=None):
    """Load a trained LSTM model from disk."""
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = VelocityLSTM().to(device)
    path = os.path.join(save_dir, "lstm_detector.pt")
    if os.path.exists(path):
        model.load_state_dict(torch.load(path, map_location=device, weights_only=True))
        model.eval()
        print(f"[LSTM] Loaded trained model from {path}")
    else:
        print(f"[LSTM] No trained model found at {path}, using random weights")
    return model


def predict_anomaly(model, velocity_sequence, device=None):
    """
    Run inference on a single velocity sequence.
    velocity_sequence: list or np.array of floats (shares-per-minute over time)
    Returns: (probability: float, is_anomaly: bool)
    """
    if device is None:
        device = next(model.parameters()).device
    model.eval()
    with torch.no_grad():
        data = torch.tensor(velocity_sequence, dtype=torch.float32)
        data = data.unsqueeze(0).unsqueeze(-1).to(device)  # (1, seq_len, 1)
        prob = model(data).item()
    return prob, prob > 0.5


# ---------------------------------------------------------------------------
# Standalone training entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  LSTM Velocity Anomaly Detector — Training")
    print("=" * 60)
    start = time.time()
    model = train_lstm(epochs=50, batch_size=128, batches_per_epoch=40)
    elapsed = time.time() - start
    print(f"\n[LSTM] Total training time: {elapsed:.1f}s")

    # Quick validation
    device = next(model.parameters()).device
    print("\n[LSTM] Quick validation:")
    normal = generate_normal_series(60, 1)[0]
    prob, is_anom = predict_anomaly(model, normal, device)
    print(f"  Normal traffic  → prob={prob:.3f}, anomaly={is_anom}")

    anomaly = generate_anomaly_series(60, 1)[0]
    prob, is_anom = predict_anomaly(model, anomaly, device)
    print(f"  Spike traffic   → prob={prob:.3f}, anomaly={is_anom}")
