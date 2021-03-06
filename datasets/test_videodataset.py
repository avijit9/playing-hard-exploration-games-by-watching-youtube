"""Test VideoDataset."""
import torch
from torch.utils.data import DataLoader

from .videodataset import VideoDataset

dataset = VideoDataset(
    filename="./videos/2AYaxTiWKoY.mp4", trim=(0, 200), crop=(0, 0, 140, 140)
)
loader = DataLoader(dataset, batch_size=32, num_workers=4)
batch = next(iter(loader))


def test_batch_type() -> None:
    """Test if the batch returned by loader is of correct type."""
    print(type(batch))
    assert type(batch) == torch.Tensor


def test_batch_dtype() -> None:
    """Test if the batch returned by loader is of correct dtype."""
    print(batch.dtype)
    assert batch.dtype == torch.float32


def test_batch_shape() -> None:
    """Test if the batch returned by loader is of correct shape."""
    print(batch.shape)
    assert batch.shape == torch.Size([32, 12, 128, 128])
