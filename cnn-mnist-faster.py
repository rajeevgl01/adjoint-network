from helper import get_data_bunch,load_data
from run import Runner, Learn
from IPython.core.debugger import set_trace
from torch import tensor, nn, optim
from callback import LR_find,Recorder,AvgStatsCallback,CudaCallback,GradientPrintCallback,ParamScheduler
import torch
import torch.nn.functional as F
from mask import randomShape,swastik,star,circle,oval,firstLayerMasking,secondLayerMasking,thirdLayerMasking
from torch.nn.parameter import Parameter
# from .. import init
from torch.autograd import gradcheck
from schedulers import combine_schedules, sched_cos
from myconv import myconv2d
from model import xresnet18
import time
from convFaster import *

class Lambda(nn.Module):
    def __init__(self, func):
        super().__init__()
        self.func = func

    def forward(self, x): return self.func(x)

def flatten(x): return x.view(x.shape[0], -1)

def flatten_parts(x): return x.view(x.shape[0],x.shape[1], -1)

def mnist_resize(x): return x.view(-1, 1, 28, 28)
def get_cnn_model(data):
    return nn.Sequential(
        Lambda(mnist_resize),
        conv2dFirstLayer( 1, 8, 5, padding=2,stride=2), nn.ReLU(), #14
        conv2dFaster( 8,16, 3, padding=1,stride=2), nn.ReLU(), # 7
        conv2dFaster(16,16, 3, padding=1,stride=2), nn.ReLU(), # 4
        #myconv2d(32,32, 5, padding=1,stride=2,mask=circle(5)), nn.ReLU(), # 2
        #nn.AdaptiveAvgPool2d(1),
        Lambda(flatten),
        linear(256,c),
    )

def lenet():
    return nn.Sequential(
        Lambda(mnist_resize),
        conv2dFirstLayer( 1, 6, 5, padding=0,stride=1),nn.ReLU(),
        nn.AvgPool2d(2,stride=2),
        conv2dFaster( 6, 16, 5, padding=0,stride=1),nn.ReLU(),
        nn.AvgPool2d(2,stride=2),
        Lambda(flatten),
        linear(256,120),nn.ReLU(),
        linear(120,84),nn.ReLU(),
        linear(84,c),
    )

def conv2(data):
    return nn.Sequential(
        Lambda(mnist_resize),
        conv2dFirstLayer( 1,64,3, padding=1,stride=1),nn.ReLU(),  # padding = same
        conv2dFaster( 64,64,3, padding=1,stride=1),nn.ReLU(),
        nn.MaxPool2d(2,stride=2),
        Lambda(flatten),
        linear(12544,256),nn.ReLU(),
        linear(256,256),nn.ReLU(),
        linear(256,c)
    )

def conv4(data):
    return nn.Sequential(
        Lambda(mnist_resize),
        conv2dFirstLayer( 1,64,3, padding=1,stride=1),nn.ReLU(),  # padding = same
        conv2dFaster( 64,64,3, padding=1,stride=1),nn.ReLU(),
        nn.MaxPool2d(2,stride=2),
        conv2dFaster( 64,128,3, padding=1,stride=1),nn.ReLU(),  # padding = same
        conv2dFaster( 128,128,3, padding=1,stride=1),nn.ReLU(),
        nn.MaxPool2d(2,stride=2),
        Lambda(flatten),
        linear(6272,256),nn.ReLU(),
        linear(256,256),nn.ReLU(),
        linear(256,c)
    )

def conv6(data):
    return nn.Sequential(
        Lambda(mnist_resize),
        conv2dFirstLayer( 1,64,3, padding=1,stride=1),nn.ReLU(),  # padding = same
        conv2dFaster( 64,64,3, padding=1,stride=1),nn.ReLU(),
        nn.MaxPool2d(2,stride=2),
        conv2dFaster( 64,128,3, padding=1,stride=1),nn.ReLU(),  # padding = same
        conv2dFaster( 128,128,3, padding=1,stride=1),nn.ReLU(),
        nn.MaxPool2d(2,stride=2),
        conv2dFaster( 128,256,3, padding=1,stride=1),nn.ReLU(),  # padding = same
        conv2dFaster( 256,256,3, padding=1,stride=1),nn.ReLU(),
        nn.MaxPool2d(2,stride=2),
        Lambda(flatten),
        linear(2304,256),nn.ReLU(),
        linear(256,256),nn.ReLU(),
        linear(256,c)
    )


if __name__ == "__main__":
   start = time.time()
   device = torch.device('cuda',0)
   torch.cuda.set_device(device)
   batch_size = 128
   c = 10
   data = get_data_bunch(batch_size)
   loss_func = MyCrossEntropy(1)
   lr_finder = False
   model = xresnet18()
   end = time.time()
   print("Loaded model", end-start)
   lr = 0.1
   lr_sched = combine_schedules([0.1, 0.9], [sched_cos(lr/10., lr), sched_cos(lr, lr/1e5)])
   lr_scheduler = ParamScheduler('lr', lr_sched)

   opt = optim.SGD(model.parameters(),lr)
   learn = Learn(model,opt,loss_func, data)
   cbfs = [lr_scheduler,CudaCallback(),AvgStatsCallback()] #cuda
   if lr_finder:
      cbfs = [CudaCallback(),LR_find(max_iters=89),Recorder()]

   run = Runner(learn,cbs = cbfs)
   run.fit(50)
   #print(model[1].weight)
   #print()
   #print(model[3].weight)
   #print()
   #print(model[5].weight)
   #print(model.layer[2].weight)

if lr_finder:
   print(cbfs[-1].lrs)
   print(cbfs[-1].losses)
