## On the Texture Bias for Few-Shot CNN Segmentation, Implemented by Reza Azad ##
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import tensorflow as tf; print(tf.__version__)
from keras import backend as K
print(K.tensorflow_backend._get_available_gpus())
import model as  M
import matplotlib.pyplot as plt
import utilz as U
import numpy as np
from parser_utils import get_parser
import pickle
import cv2

## Get options
options = get_parser().parse_args()
t_l_path   = './fss_test_set.txt'
Best_performance = 0
Valid_miou = []
encoder = 'VGG_b345' #'RN' # 'VGG_b345' #'RN' # 'VGG_b345' #'RN' #
weights = '/content/drive/MyDrive/' + encoder  + "_"+ str(5) +"_" +'fewshot_DOGLSTM.h5'
# Build the model
model = M.my_model(encoder = encoder, input_size = (options.img_h, options.img_w, 3), k_shot = options.kshot, learning_rate = options.learning_rate)
model.summary()
if os.path.isfile(weights):
  model.load_weights(weights)

# Load an episode of train
Train_list, Test_list = U.Get_tr_te_lists(options, t_l_path)


# Train on episodes
def train(opt):
    for ep in range(opt.epochs):
        epoch_loss = 0
        epoch_acc  = 0
        ## Get an episode for training model
        for idx in range(opt.iterations):
            support, smask, query, qmask = U.get_episode(opt, Train_list)
            acc_loss = model.train_on_batch([support, smask, query], qmask)
            epoch_loss += acc_loss[0]
            epoch_acc  += acc_loss[1]
            if (idx % 50) == 0:
                print ('Epoch>>',(ep+1),'>> Itteration:', (idx+1),'/',opt.iterations,' >>> Loss:', epoch_loss/(idx+1), ' >>> Acc:', epoch_acc/(idx+1))
        evaluate(opt, ep)

def evaluate(opt, ep):
    global Best_performance
    global Valid_miou
    overall_miou = 0.0
    for idx in range (opt.it_eval):
        ## Get an episode for evaluation 
        support, smask, query, qmask = U.get_episode(opt, Test_list)
        # Generate mask 
        Es_mask = model.predict([support, smask, query])
        # Compute MIOU for episode
        ep_miou       = U.compute_miou(Es_mask, qmask)
        overall_miou += ep_miou
    print('Epoch:', ep+1 ,'Validation miou >> ', (overall_miou / opt.it_eval))  
    weights = '/content/drive/MyDrive/' + encoder  + "_"+ str(ep+1) +"_" +'fewshot_DOGLSTM.h5'
    try:
      model.save_weights(weights)
    except:
      print("skipped saving: " + weights)
      pass

def test(opt):
    model.load_weights(weights)
    overall_miou = 0.0
    for idx in range (opt.it_test):
        ## Get an episode for test 
        support, smask, query, qmask = U.get_episode(opt, Test_list)
        # Generate mask 
        Es_mask = model.predict([support, smask, query])
        # Compute MIOU for episode
        ep_miou       = U.compute_miou(Es_mask, qmask)
        overall_miou += ep_miou
        print(Es_mask.shape)
        print("-------------------")
        print(qmask.shape)
        print('episode>>',(idx+1) ,'miou>>', ep_miou)
        Es_mask = np.where(Es_mask > 0.6, 1 , 0.)
        Es_mask = Es_mask * 255
        O = Es_mask[0]
        for idx in range(Es_mask.shape[0]):
          O = O + Es_mask[idx]
        
        O = O.astype(np.uint8)
        O = cv2.cvtColor(O, cv2.COLOR_GRAY2RGBA)
        r = O.copy()
        r[:, :, 0] = 0
        r[:, :, 2] = 0
        cv2.imwrite("m.png", r)
        break;

    #print('Test miou >> ', (overall_miou / opt.it_test))    


train(options) 
test(options) 
#Performance = {}
#Performance['Valid_miou'] = Valid_miou

#with open('performance_DOGLSTM.pkl', 'wb') as f:
#        pickle.dump(Performance, f, pickle.HIGHEST_PROTOCOL)

