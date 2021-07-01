import torch
from torch import nn
import math
class GRUModel(nn.Module):
    def __init__(self, model_config, device, type_model):
        super(GRUModel,self).__init__()
        self.input_dim = model_config['input_dim']
        self.hidden_units = model_config['num_units']
        self.num_classes = model_config['num_classes']
        self.num_outputs = model_config['num_outputs']
        self.feature_size = model_config['feature_size']
        self.num_inputs = model_config['num_inputs']
        self.output_points_fw = model_config['output_points_fw']
        self.output_points_bw = model_config['output_points_bw']
        self.region = model_config['region']
        self.device = device
        self.num_layers = 3 
        self.linear = nn.Linear(self.input_dim, self.feature_size, bias=True)
        self.batch_norm = nn.BatchNorm1d(self.feature_size)
        self.leaky_relu = nn.LeakyReLU(negative_slope=0.01)
        self.sigmoid = nn.Sigmoid()
        self.batch_norm_list = nn.ModuleList([nn.BatchNorm1d(self.hidden_units*2) for _ in range(self.num_layers)])
        self.num_encode = 10
        self.gru = nn.ModuleList(self._create_gru_cell(
            self.feature_size, 
            self.hidden_units,
            self.num_layers
        ))
        self.list_linear = nn.ModuleList(self._create_linear_list(
            self.hidden_units,
            self.num_classes,
            self.output_points_fw,
            self.output_points_bw
        ))

    @staticmethod
    def _create_gru_cell(input_size, hidden_units, num_layers):
        gru = [nn.GRU(input_size, hidden_units, bidirectional=True)] # First layer
        gru += [nn.GRU(hidden_units*2, hidden_units, bidirectional=True) for _ in range(num_layers-1)] # 2 -> num_layers
        return gru

    @staticmethod
    def _create_linear_list(hidden_units, num_classes, output_points_fw, output_points_bw):
        list_linear = []
        for (t_fw, t_bw) in (zip(output_points_fw, output_points_bw)):
            if (t_fw is not None) and (t_bw is not None) and (not math.isnan(t_fw)) and (not math.isnan(t_bw)):
                list_linear.append(nn.Linear(hidden_units*2, num_classes, bias=True)) 
            else:
                list_linear.append(nn.Linear(hidden_units, num_classes, bias=True))
        return list_linear

    def forward(self, x):
        '''
            return logits_list(g)  in paper
        '''
        print(x.shape)
        gru_inputs = self.linear(x)
        gru_inputs = self.leaky_relu(gru_inputs)
        outputs, _ = self._compute_gru(self.gru, gru_inputs)
        
        logit_list = []
        for index, (t_fw, t_bw) in enumerate(zip(self.output_points_fw, self.output_points_bw)):
            gru_output = []
            if t_fw is not None and not math.isnan(t_fw):
                gru_output.append(outputs[:, int(t_fw), :self.hidden_units]) 
            if t_bw is not None and not math.isnan(t_bw):
                gru_output.append(outputs[:, int(t_bw), self.hidden_units:])
            gru_output = torch.cat(gru_output, dim=1).to(self.device)
            logit = self.list_linear[index](gru_output)
            logit_list.append(logit)
        print(torch.stack(logit_list).shape)
        return logit_list

    def init_hidden(self, batch):
        weight = next(self.parameters()).data
        hidden = weight.new(2, batch, self.hidden_units).zero_()
        return hidden
    
    def _compute_gru(self, GRUs, _input):
        batch_size = _input.shape[0]
        hidden = self.init_hidden(batch_size)
        for i, gru in enumerate(GRUs):
            output, state = gru(_input)
            if i > 0:
                _input = _input + output
            else:
                _input = output
            hidden = state 
        return _input, hidden

# /** 
# *                   _ooOoo_
# *                  o8888888o
# *                  88" . "88
# *                  (| -_- |)
# *                  O\  =  /O
# *               ____/`---'\____
# *             .'  \\|     |//  `.
# *            /  \\|||  :  |||//  \
# *           /  _||||| -:- |||||-  \
# *           |   | \\\  -  /// |   |
# *           | \_|  ''\---/''  |   |
# *           \  .-\__  `-`  ___/-. /
# *         ___`. .'  /--.--\  `. . __
# *      ."" '<  `.___\_<|>_/___.'  >'"".
# *     | | :  `- \`.;`\ _ /`;.`/ - ` : | |
# *     \  \ `-.   \_ __\ /__ _/   .-` /  /
# *======`-.____`-.___\_____/___.-`____.-'======
# *                   `=---='
# *^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# * Buddha blessing never BUG
# */