#!/usr/bin/env python3
"""
Plot t-SNE to check embedding quality.

TODO Separate TDC, CMC, TDC+CMC
"""
from typing import Any, List, Tuple

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
import wandb
from sklearn.manifold import TSNE
from torch.utils.data import DataLoader

from commons import load_models
from datasets import VideoAudioDataset
from networks import CMC, TDC


def get_tsne_loaders(
    filenames: List[str],
    trims: List[Tuple[int, int]],
    crops: List[Tuple[int, int, int, int]],
) -> List[Any]:
    """
    Get TSNE dataloaders.

    Parameters
    ----------
    filenames: list of str
        Filenames of videos to use.
    trims: list of tuple
        Specify frame indices to use.
    crops: list of tuple
        Specify which part of image to use.

    """
    datasets = [
        VideoAudioDataset(filename, trim, crop, frame_rate=15)
        for filename, trim, crop in zip(filenames, trims, crops)
    ]
    loaders = [
        DataLoader(dataset, batch_size=32, shuffle=False, num_workers=1)
        for dataset in datasets
    ]

    return loaders


def plot_tsne(
    tsne_loaders: List[Any],
    tdc: Any,
    cmc: Any,
    device: Any,
    save: bool = False,
    log_to_wandb: bool = True,
) -> None:
    """
    Plot t-SNE of given dataloaders.

    TODO Fix docstrings

    """
    embeds = []
    for loader in tsne_loaders:
        embed_batches = []
        for _, batch in enumerate(loader):
            stack_batch, sample_batch = batch
            stack_embed_batch = tdc(stack_batch.to(device))
            sample_embed_batch = cmc(sample_batch.to(device))
            embed_batch = torch.cat((stack_embed_batch, sample_embed_batch), dim=1)
            embed_batch = F.normalize(embed_batch).cpu().detach().numpy()
            embed_batches.append(embed_batch)
        embed = np.concatenate(embed_batches, axis=0)
        embeds.append(embed)

    # Embed video frames with t-SNE
    tsne_embeds = TSNE(n_components=2).fit_transform(np.concatenate(embeds, axis=0))

    # Scatterplot with different colors
    xs, ys = zip(*tsne_embeds)
    scatter_colors = cm.rainbow(np.linspace(0, 1, len(embeds)))

    embed_sizes = [len(embed) for embed in embeds]
    embed_indices = [0] + np.cumsum(embed_sizes).tolist()
    for i, _ in enumerate(embed_sizes):
        xs_part = xs[embed_indices[i] : embed_indices[i + 1]]
        ys_part = ys[embed_indices[i] : embed_indices[i + 1]]
        plt.scatter(xs_part, ys_part, c=[scatter_colors[i]], s=10)

    # Save and show completed plot
    if save:
        plt.savefig("tsne.png")
    if log_to_wandb:
        wandb.log({"t-SNE": plt})


if __name__ == "__main__":
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    # Load Models
    tdc = TDC().to(device)
    cmc = CMC().to(device)
    load_models(tdc, cmc)

    # Set to evaluation mode
    tdc.eval()
    cmc.eval()

    filenames = [
        "./data/6zXXZvVvTFs",
        "./data/SuZVyOlgVek",
        "./data/2AYaxTiWKoY",
        "./data/pF6xCZA72o0",
    ]
    trims = [(960, 1403), (15, 437), (550, 1515), (1465, 2201)]
    crops = [
        (35, 50, 445, 300),
        (79, 18, 560, 360),
        (0, 13, 640, 335),
        (20, 3, 620, 360),
    ]
    tsne_loaders = get_tsne_loaders(filenames, trims, crops)
    plot_tsne(tsne_loaders, tdc, cmc, device, True, False)
