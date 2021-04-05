import os
import sys
sys.path.append("data")
sys.path.append("model")

import json
from model.HybridModel import HybridModel
from data.dataset import RegionDataset
import torch
from torch.utils.data import DataLoader
from torch import nn

def train(dataloader, model_config, batch_size=1,input_size=2, hidden_units=40):
    """
        input_size: number of features
        batch_size: number of samples
    """

    model = HybridModel(model_config, batch_size=batch_size).float()
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    for t in range(200):
        for batch, (X, y) in enumerate(dataloader):
            # Compute prediction error
            prediction = model(X.float())          
            loss = loss_fn(prediction[0,:].float(), y[0,:,1].long())

            # Backpropagation
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        loss = loss.item()
        print(f"[EPOCHS {t}]: loss: {loss:>7f}")
    

def main():
    root_dir = 'data/org_data'
    model_config_dir = 'model/config/region_1_config.json'
    with open(model_config_dir, "r") as json_config:
        model_config = json.load(json_config)
    dataset = RegionDataset(root_dir)
    batch_size = 1
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    train(dataloader, model_config, batch_size)
if __name__ == "__main__":
    main()