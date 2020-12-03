## On the Texture Bias for Few-Shot CNN Segmentation, Implemented by Reza Azad ##
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import tensorflow.keras
import tensorflow.keras.backend as K
K.set_floatx('float16')
import tensorflow.keras.layers as layers 
from tensorflow.keras.models import *
from tensorflow.keras.layers import *
import tensorflow.keras.backend  as backend
import encoder_models as EM
import cv2
import numpy as np


def RN_GlobalAveragePooling2D_r(f):
    def func(x):
        x    =  layers.multiply([x, f])
        repx =  int(x.shape[2])
        repy =  int(x.shape[3])
        x    = (backend.sum(x, axis=[2, 3], keepdims=True) / (backend.sum(f, axis=[2, 3], keepdims=True)))
        x    =  backend.repeat_elements(x, repx, axis = 2)
        x    =  backend.repeat_elements(x, repy, axis = 3)    
        return x
    return Lambda(func) 

def GlobalAveragePooling2D_r(f):
    def func(x):
        repc =  int(x.shape[4])
        #print("f.shape")
        #print(f.shape)
        m    =  backend.repeat_elements(f, repc, axis = 4)
        #print("GAP")
        #print(x.shape)
        #print(m.shape)
        x    =  layers.multiply([x, m])
        repx =  int(x.shape[2])
        repy =  int(x.shape[3])
        x    = (backend.sum(x, axis=[2, 3], keepdims=True) / (backend.sum(m, axis=[2, 3], keepdims=True)))
        x    =  backend.repeat_elements(x, repx, axis = 2)
        x    =  backend.repeat_elements(x, repy, axis = 3)    
        return x
    return Lambda(func)

def Rep_mask(f):
    def func(x):
        x    =  backend.repeat_elements(x, f, axis = 1)   
        return x
    return Lambda(func)
        
def get_kernel_gussian(kernel_size, Sigma=1, in_channels = 128):
    kernel_weights = cv2.getGaussianKernel(ksize=kernel_size, sigma= Sigma)
    kernel_weights = kernel_weights * kernel_weights.T
    kernel_weights = np.expand_dims(kernel_weights, axis=-1)
    kernel_weights = np.repeat(kernel_weights, in_channels, axis=-1)
    kernel_weights = np.expand_dims(kernel_weights, axis=-1)
    return kernel_weights
    
def common_representation(x1, x2): 
    repc =  int(x1.shape[1])
    x2   =  keras.layers.Reshape(target_shape=(1, np.int32(x2.shape[1]), np.int32(x2.shape[2]), np.int32(x2.shape[3]))) (x2) 
    x2   =  Rep_mask(repc)(x2)
    print(x1.shape)
    print(x2.shape)
    x    =  layers.concatenate([x1, x2], axis=4) 
    x    =  layers.TimeDistributed(layers.Conv2D(128, 3, padding = 'same', kernel_initializer = 'he_normal'))(x)
    x    =  layers.TimeDistributed(layers.BatchNormalization(axis=3))(x) 
    x    =  layers.TimeDistributed(layers.Activation('relu'))(x) 
    return x
   
def my_model(encoder = 'VGG', input_size = (256, 256, 1), k_shot = 1, learning_rate = 1e-4):
    # Get the encoder
    encoder_t = encoder
    if encoder_t == 'VGG_b3':
       encoder = EM.vgg_encoder_b3(input_size = input_size)
    elif encoder_t == 'VGG_b4':
       encoder = EM.vgg_encoder_b4(input_size = input_size)
    elif encoder_t == 'VGG_b34':
       encoder = EM.vgg_encoder_b34(input_size = input_size)
    elif encoder_t == 'VGG_b5':
       encoder = EM.vgg_encoder_b5(input_size = input_size)
    elif encoder_t == 'VGG_b345':
       encoder = EM.vgg_encoder_b345(input_size = input_size)
    elif encoder_t == 'VGG_b35':
       encoder = EM.vgg_encoder_b35(input_size = input_size)
    elif encoder_t == 'VGG_b45':
       encoder = EM.vgg_encoder_b45(input_size = input_size)
    elif encoder_t == 'RN':
       encoder = EM.rn_encoder(input_size = input_size)
    else:
       print('Encoder is not defined yet')



    I_mask   = layers.Input((k_shot, int(input_size[0]/4), int(input_size[1]/4), 1))
    O_mask = ''
    print(I_mask.shape)
    if encoder_t == 'RN':
      #print(S_mask.shape)
      #ksm_encoder = keras.models.Sequential()
      #sm_enc = 
      #sm_enc = layers.Conv2D(128, (7, 7), strides=(2, 2), name='conv_sm')
      enc = layers.Conv2D(128, (8, 8), strides=(7, 7))
      ksm_encoder_layer = layers.TimeDistributed(enc, input_shape=(k_shot, int(input_size[0]/4), int(input_size[1]/4), 1))
      O_mask = ksm_encoder_layer(I_mask)
      print("134")
      print(O_mask.shape)
    else:
      O_mask = I_mask

    model_S = Model(inputs=[I_mask], outputs=O_mask)
    S_mask = O_mask
    S_input  = layers.Input((k_shot, input_size[0], input_size[1], input_size[2]))
    #print(S_input.shape)
    Q_input  = layers.Input(input_size)

    #print(S_mask.shape)
    ## K shot


    kshot_encoder = Sequential()
    kshot_encoder.add(layers.TimeDistributed(encoder, input_shape=(k_shot, input_size[0], input_size[1], input_size[2])))

    ## Encode support and query sample
    s_encoded = kshot_encoder(S_input)
    q_encoded = encoder(Q_input)
    s_encoded = layers.TimeDistributed(layers.Conv2D(128, (3, 3), activation='relu', padding='same'))(s_encoded)
    q_encoded = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(q_encoded) 

    ## Difference of Gussian Pyramid parameters
    kernet_shapes = [3, 5, 7, 9]
    k_value = np.power(2, 1/3)
    sigma   = 1.6
    
    ## Kernel weights for Gussian pyramid
    Sigma1_kernel = get_kernel_gussian(kernel_size = kernet_shapes[0], Sigma = sigma*np.power(k_value, 1), in_channels = 128)
    Sigma2_kernel = get_kernel_gussian(kernel_size = kernet_shapes[1], Sigma = sigma*np.power(k_value, 2), in_channels = 128)    
    Sigma3_kernel = get_kernel_gussian(kernel_size = kernet_shapes[2], Sigma = sigma*np.power(k_value, 3), in_channels = 128)     
    Sigma4_kernel = get_kernel_gussian(kernel_size = kernet_shapes[3], Sigma = sigma*np.power(k_value, 4), in_channels = 128)        
    
    Sigma1_layer  = layers.TimeDistributed(layers.DepthwiseConv2D(kernet_shapes[0], use_bias=False, padding='same'))
    Sigma2_layer  = layers.TimeDistributed(layers.DepthwiseConv2D(kernet_shapes[1], use_bias=False, padding='same'))
    Sigma3_layer  = layers.TimeDistributed(layers.DepthwiseConv2D(kernet_shapes[2], use_bias=False, padding='same'))
    Sigma4_layer  = layers.TimeDistributed(layers.DepthwiseConv2D(kernet_shapes[3], use_bias=False, padding='same'))

    ## Gussian filtering
    x1 = Sigma1_layer(s_encoded)
    x2 = Sigma2_layer(s_encoded)
    x3 = Sigma3_layer(s_encoded)    
    x4 = Sigma4_layer(s_encoded)    

      #S_mask = smx
      #print(S_mask.shape)

    #print("x1.shape")
    #print(x1.shape)
    #print(s_encoded.shape)


    DOG1 = layers.Subtract()([s_encoded, x1])
    DOG2 = layers.Subtract()([x1, x2])
    DOG3 = layers.Subtract()([x2, x3])            
    DOG4 = layers.Subtract()([x3, x4])   
    #print("Dog.shape") 
    #print(S_mask.shape)
    #print(DOG1.shape)
    
    s_1 =''
    s_2 =''
    s_3 =''
    s_4 =''
    ## Global Representation
    if encoder_t == 'RN':
      s_1  = RN_GlobalAveragePooling2D_r(S_mask)(DOG1)   
      s_2  = RN_GlobalAveragePooling2D_r(S_mask)(DOG2)
      s_3  = RN_GlobalAveragePooling2D_r(S_mask)(DOG3)
      s_4  = RN_GlobalAveragePooling2D_r(S_mask)(DOG4)
    else:

      s_1  = GlobalAveragePooling2D_r(S_mask)(DOG1)   
      s_2  = GlobalAveragePooling2D_r(S_mask)(DOG2)
      s_3  = GlobalAveragePooling2D_r(S_mask)(DOG3)
      s_4  = GlobalAveragePooling2D_r(S_mask)(DOG4)

    ## Common Representation of Support and Query sample
    s_1  = common_representation(s_1, q_encoded)
    s_2  = common_representation(s_2, q_encoded)
    s_3  = common_representation(s_3, q_encoded)
    s_4  = common_representation(s_4, q_encoded)        
        
    ## Bidirectional Convolutional LSTM on Pyramid      
    s_3D   = layers.concatenate([s_1, s_2, s_3, s_4], axis=1) 

    LSTM_f = layers.ConvLSTM2D(filters = 128, kernel_size=(3, 3), padding='same', return_sequences = False, 
    go_backwards = False, kernel_initializer = 'he_normal')(s_3D)    

    LSTM_b = layers.ConvLSTM2D(filters = 128, kernel_size=(3, 3), padding='same', return_sequences = False, 
    go_backwards = True,  kernel_initializer = 'he_normal')(s_3D)
    Bi_rep = layers.Add()([LSTM_f, LSTM_b])  

    ## Decode to query segment
    x = layers.Conv2D(128, 3, padding = 'same', kernel_initializer = 'he_normal')(Bi_rep)
    x = layers.BatchNormalization(axis=3)(x) 
    x = layers.Activation('relu')(x)       
    x = layers.UpSampling2D(size=(2*2, 2*2))(x)
    x = layers.Conv2D(128, 3, padding = 'same', kernel_initializer = 'he_normal')(x)
    x = layers.BatchNormalization(axis=3)(x) 
    x = layers.Activation('relu')(x)    
    x = layers.UpSampling2D(size=(2*4, 2*4))(x)
    x = layers.Conv2D(128, 3, padding = 'same', kernel_initializer = 'he_normal')(x)
    x = layers.BatchNormalization(axis=3)(x) 
    x = layers.Activation('relu')(x)       
    x = layers.Conv2D(64, 3,  activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(x)
    x = layers.Conv2D(2, 3,   activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(x)
    final = layers.Conv2D(1, 1,   activation = 'sigmoid')(x) 
    print("AAA") 
    print(final.shape)
    seg_model = Model(inputs=[S_input, I_mask, Q_input], outputs = final)
    ## Load Guassian weights and make it unlearnable
    Sigma1_layer.set_weights([Sigma1_kernel])
    Sigma2_layer.set_weights([Sigma2_kernel])
    Sigma3_layer.set_weights([Sigma3_kernel])
    Sigma4_layer.set_weights([Sigma4_kernel])
    Sigma1_layer.trainable = False
    Sigma2_layer.trainable = False 
    Sigma3_layer.trainable = False
    Sigma4_layer.trainable = False 

    seg_model.compile(optimizer = keras.optimizers.Adam(lr = learning_rate), loss = 'binary_crossentropy', metrics = ['accuracy']) 
    
    return seg_model    
    
    
    
    