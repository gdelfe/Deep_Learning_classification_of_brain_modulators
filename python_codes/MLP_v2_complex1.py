#!/usr/bin/env python

import numpy as np
import torch
from torch import nn, optim
from torchvision import transforms
import torch.nn.functional as F
import matplotlib.pyplot as plt
from torch.utils.data import TensorDataset, DataLoader
import os
from random import shuffle
import pylab
from mpl_toolkits.axes_grid1 import make_axes_locatable
from sklearn.model_selection import train_test_split

import import_data_sets1 as data
import ANN_Models as ANN

#%%
# ## DATA 

# PATH DIRECTORY 
Sess = 15
Ch = 34
# maxCh = 20
# format image (resolution):
x_size = 47
y_size = 30

train_s = 0.75
test_s = 1 - train_s

rand_max = 100
brain_area = 'OFC'
# LOAD DATA
# tensor_hit_train, tensor_hit_test, tensor_miss_train, tensor_miss_test = data.load_data_NW(Sess,Ch,x_size,y_size,train_s,test_s)
# tensor_hit_train, tensor_hit_test, tensor_miss_train, tensor_miss_test = data.load_data_area(Sess,brain_area, x_size, y_size, train_s, test_s)
# tensor_hit_trainA, tensor_hit_testA, tensor_miss_trainA, tensor_miss_testA = data.load_data_random_NW(Sess,Ch,x_size,y_size,train_s,test_s,rand_max)
# tensor_hit_trainA, tensor_hit_testA, tensor_miss_trainA, tensor_miss_testA = data.load_data_homogeneous(Sess,Ch,x_size,y_size,train_s,test_s)
# tensor_hitA, tensor_missA = data.load_data_homogeneous_complex(Sess,Ch,x_size,y_size)
tensor_hit_trainA, tensor_hit_testA, tensor_miss_trainA, tensor_miss_testA = data.load_data_random_complex(Sess,Ch,x_size,y_size,train_s,test_s,rand_max)


#%%
print(tensor_hit_trainA.shape)
print(tensor_hit_testA.shape)
print(tensor_miss_trainA.shape)
print(tensor_miss_testA.shape)


#%%
# Remove first element because it is empty
tensor_missA = tensor_missA[1:]
tensor_hitA = tensor_hitA[1:]

# ### Balance the data set
tensor_hitA = tensor_hitA[0:tensor_missA.shape[0]]


print('Data set size after balancing')
print(tensor_hitA.shape)
print(tensor_missA.shape)

#%%
fmin = 0
fmax = 30

tmin = 0
tmax = 47

#%%

# Re_hit = np.full((43,47,30,1),0.5)
# Im_hit = np.full((43,47,30,1),1.5)

# tensor_hit = np.concatenate((Re_hit,Im_hit),axis=3)

# Re_miss = np.full((43,47,30,1),0.2)
# Im_miss = np.full((43,47,30,1),1.5)

# tensor_miss = np.concatenate((Re_miss,Im_miss),axis=3)

# tensor_hit = np.concatenate((Re_hit,Im_hit),axis=3)

#%%
# copy data onto new tensors
tensor_hit = tensor_hitA[:,tmin:tmax,fmin:fmax,:].copy()
tensor_miss = tensor_missA[:,tmin:tmax,fmin:fmax,:].copy()

# tensor_hit = np.expand_dims(tensor_hit, axis=3)
# tensor_miss = np.expand_dims(tensor_miss, axis=3)

plt.imshow(tensor_missA[0,:,:,0].transpose(),origin='lower')
plt.show()
plt.imshow(tensor_miss[0,:,:,1].transpose(),origin='lower')
plt.show()

print(tensor_hit.shape)
print(tensor_miss.shape)

#%%
# ### Generate the labels
# Generate the labels for hits and misses and stack them into a single array

labels_hit = np.ones(tensor_hit.shape[0],dtype='l')
labels_miss = np.zeros(tensor_miss.shape[0],dtype='l')

# labels_hit = np.zeros(tensor_hit.shape[0],dtype='l')
# labels_miss = np.ones(tensor_miss.shape[0],dtype='l')

print('Labels')
print(labels_hit.shape)
print(labels_miss.shape)

# total labels for hits and misses
labels_tot = np.append(labels_hit,labels_miss)
print(labels_tot.shape)
#%%

# ################################################
# # ### Normalize inputs
# ################################################

for z in range(0,2): # for both the real and imaginary dimension
    for indx in range(tensor_hit.shape[0]):
        mean = np.mean(tensor_hit[indx,:,:,z])
        std = np.std(tensor_hit[indx,:,:,z])
        tensor_hit[indx,:,:,z] = (tensor_hit[indx,:,:,z] - mean)/std
        
    for indx in range(tensor_miss.shape[0]):
        mean = np.mean(tensor_miss[indx,:,:,z])
        std = np.std(tensor_miss[indx,:,:,z])
        tensor_miss[indx,:,:,z] = (tensor_miss[indx,:,:,z] - mean)/std

# plot the real part normalized
img = plt.imshow(tensor_hit[0,:,:,0].transpose(),origin='lower')
plt.colorbar(img,orientation="horizontal")
plt.show()
# plot the imaginary part normalized
plt.imshow(tensor_hit[0,:,:,0].transpose(),origin='lower')
plt.colorbar(img,orientation="horizontal")
plt.show()

#%%
# =============================================================================
# ## Split train and test set 
# =============================================================================

tensor_tot = np.concatenate((tensor_hit,tensor_miss),axis=0) # stack matrix along the 1st dimension 

X_train, X_test, y_train, y_test = train_test_split(tensor_tot,labels_tot, test_size=0.25, random_state = 4,stratify=labels_tot)
y_train.astype('l')
y_test.astype('l')

print ('Train set:', X_train.shape,  y_train.shape)
print ('Test set:', X_test.shape,  y_test.shape)

#%%
################################################
# ## Load data into a trainloader and testloader
################################################


class CustomDataset(torch.utils.data.Dataset):
    def __init__(self, data):
        self.data = data

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)


# Create datasets
# train_dataset = CustomDataset((X_train,y_train))
# test_dataset = CustomDataset((X_test,y_test))

X_train = torch.tensor(X_train)
y_train = torch.tensor(y_train)
X_test = torch.tensor(X_test)
y_test = torch.tensor(y_test)

train_dataset = TensorDataset(X_train,y_train)
test_dataset = TensorDataset(X_test,y_test)
# create train and test loaders
trainloader = DataLoader(train_dataset, shuffle=True, batch_size=50)
testloader = DataLoader(test_dataset, shuffle=True, batch_size=50)

#%%

################################################
# ### Create iterable as a test 
################################################

# The batch_size decides how many images in the batch during the training or test.
# The numb of iteration in each train (test) loader are: tot length of train (test) data / batch_size. So if the tot number of data is 2000 and the batch size is 50, the iteration on the dataloader is done 40 times, each time 50 images are loaded 

batch_size = 2
images, labels = next(iter(trainloader))

for b in range(batch_size):
    plt.imshow(images[b,:,:,0].numpy().transpose(),origin='lower')
    plt.colorbar(img,orientation="horizontal")
    plt.show()
    print('Batch: ',b)
    print('Label: ',labels[b].item())
    print()
print(labels.shape)
print(images.shape)
print(labels[0])


print(images.shape)


print(images.view(images.shape[0],-1).shape)
images.shape[1]


#%%
# +++++++++++++++++++++++++++++++++++++++++++++
################################################
# # MODELS
################################################

#%%
# ### Linear regression

model = ANN.Linear_Regression(X_train.shape[1],X_train.shape[2],2)
print(model)


#%%

# ### Multilayer perceptron (with dropout)

model = ANN.MLP(X_train.shape[1],X_train.shape[2],2,0.2)
print(model)

#%%
# ### Multilayer perceptron (with dropout)

model = ANN.MLP_deep(X_train.shape[1],X_train.shape[2],2,0.2)
print(model)


#%%
# ### Udacity multilayer perceptron 

model = ANN.Classifier()
print(model)


#%%
# ## CONVOLUTIONAL NETWORKS

model = ANN.CNN()
print(model)


#%%
# ## CONVOLUTIONAL NETWORKS

model = ANN.CNN_small()
print(model)

#%%
# ## CONVOLUTIONAL NETWORKS

model = ANN.CNN_deep()
print(model)


#%%
################################################
# ### Set loss function and optimizer

criterion = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(model.parameters(), lr = 0.001, weight_decay = 0.2)


################################################
# #### Move model on GPU if available 

# check if CUDA is available
train_on_gpu = torch.cuda.is_available()

if not train_on_gpu:
    print('CUDA is not available.')
else:
    print('CUDA is available!')

# move tensors to GPU if CUDA is available
if train_on_gpu:
    model.cuda()
    print('Moving model on GPU...')
next(model.parameters()).is_cuda
train_on_gpu

################################################
# ### Define accuracy

def binary_acc(logits, labels):
    y_pred_tag = torch.round(torch.sigmoid(logits)) # make probability out of logits and then round to 0 or 1

    correct_results_sum = (y_pred_tag == labels).sum().float()
    acc = correct_results_sum/labels.shape[0]
    acc = torch.round(acc * 100)
    
    return acc


print('Train dataset length: ',len(train_dataset))
print('Test dataset length: ',len(test_dataset))
print('Trainloader length: ', len(trainloader))
print('Testloader length: ', len(testloader))


#%%
################################################
# ## Reset the weights to random numbers

def weights_init(m):
    if isinstance(m, nn.Linear):
        torch.nn.init.xavier_uniform_(m.weight.data)

torch.manual_seed(90)
model.apply(weights_init)


next(model.parameters()).is_cuda
print(model)


#%%
################################################
# ## Train and validate the Network 
################################################
# Training and Testing is done on the fly:
# For each epoch the model is trained (the loss is computed by using the training set) and it is tested (the loss and accuracy are computed by using the test set), in order to compare training loss with testing loss and decide when to stop the training and avoid overfitting. 


#######################
#     TRAINING  
######################

model.train() # set the network in training mode

epochs = 110
train_losses, test_losses, acc_list = [], [], []

for epoch in range(1,epochs+1):
    running_loss = 0
    for images, labels in trainloader:
        
        #         labels = labels.long() # change label type from int to long 
        images = images.type(torch.FloatTensor)
        labels = labels.type(torch.FloatTensor) # convert labels to Float for BCELoss

        
        if train_on_gpu: # move data on GPU
            images, labels = images.cuda(), labels.cuda()
              
        # Clear the gradients
        optimizer.zero_grad()
        
        # logits, conv_x1, conv_x2, conv_x3 = model(images) # forward pass - conv deep
        logits, conv_x1, conv_x2 = model(images) # forward pass - conv small
        # logits = model(images) # forward pass - LR, MLP
        loss = criterion(torch.squeeze(logits),labels) # compute the loss
        loss.backward() # backpropagate to compute the gradients
        optimizer.step() # update the weights
        
        running_loss =+ loss.item()
    
    else:
        
        #######################
        #     VALIDATION 
        ######################
 
        test_loss = 0
        accuracy = 0
        epoch_acc = 0
        with torch.no_grad(): # set the tracing of gradients to zero
            model.eval() # set the dropout to OFF, i.e. model is in evaluation mode
            

            for images, labels in testloader:
                
#                 for b in range(batch_size):
#                     plt.imshow(np.flipud(images[b].numpy().transpose()))
#                     plt.show()
                images = images.type(torch.FloatTensor)
                labels = labels.type(torch.FloatTensor) # convert labels to Float for BCELoss    
#                 labels = labels.long() # change label type from int to long 
    
                if train_on_gpu: # move data on GPU
                    images, labels = images.cuda(), labels.cuda()
                

                
#                 print('\n\n************ New batch....\n')
                # logits, conv1, conv2, conv3 = model(images) # forward pass - conv deep
                logits, conv1, conv2 = model(images) # forward pass - conv small
                # logits = model(images) # forward pass - LR, MLP
                logits = torch.squeeze(logits)
                valid_loss = criterion(logits,labels)
                test_loss += valid_loss.item()    

                y_pred_tag = torch.round(torch.sigmoid(logits)) # make probability out of logits and then round to 0 or 1

#                 print('y_pred : \n',y_pred_tag)
#                 print()
#                 print('labels: ',labels)

#                 print('Test loss: ',test_loss)

#                 print()
#                 print('top_p: \n',top_p)
#                 print('top_class :\n',torch.transpose(top_class,1,0))
#                 print()
#                 
                
#   
                acc = binary_acc(logits,labels) # accuracy for each batch
#                 print('accuracy',acc)
                epoch_acc += acc.item() # sum up the accuracies across batches

                
        model.train() # set the model back to train mode, i.e. dropout is ON
        train_losses.append(running_loss/len(trainloader))
        test_losses.append(test_loss/len(testloader))
        acc_list.append(epoch_acc/len(testloader))
            
        accuracy = 0
        ############################
        # PRINT ACCURACTY AND LOSSES
        ############################
#         if epoch % 10 == 0:
        print("Epoch: {}/{}.. ".format(epoch+1, epochs),
              "Training Loss: {:.7f}.. ".format(running_loss/len(trainloader)),
              "Test Loss: {:.5f}.. ".format(test_loss/len(testloader)),
              "Test Accuracy: {:.3f}".format(epoch_acc/len(testloader)))
        
        ep = np.arange(1,epoch+1)

        fig, (ax1,ax2,ax3) = plt.subplots(1,3,figsize=(13,4))
        # ax = plt.subplot(111)
        ax1.plot(ep,train_losses,'r^--',linewidth=2,label = 'Train loss')
        ax1.set_xlabel('epochs',fontsize=12)
        ax1.set_ylabel('Loss',fontsize=13)
        ax1.set_title('Train loss',fontsize=16)
        ax1.legend()
        ax1.grid(True)

        ax2.plot(ep,test_losses,'go--',linewidth=2,label = 'Test loss')
        ax2.set_xlabel('epochs',fontsize=12)
        ax2.set_title('Test loss',fontsize=16)
        ax2.legend()
        ax2.grid(True)
        
        ax3.plot(ep,acc_list,'bo--',linewidth=2,label = 'Accuracy')
        ax3.set_xlabel('epochs',fontsize=12)
        ax3.set_title('Accuracy',fontsize=16)
        ax3.legend()
        ax3.grid(True)

        plt.show()


#%%
# =============================================================================
# # ### Plot Train loss, Test loss, and Accuracy
# =============================================================================

NN = 'MLPd'
filter1 = 4
filter2 = 8

dir_data = 'Shaoyu_data/Plots'
directory = '/random_N015_W_25_dn_018_k_6'
dir_frequency = '/complex/frequency_0_60'
# dir_tapers = '/tapers_3_4'
parameters = 'Re and Im, Ch=34, 50 rand, N=0.15, W=25, dn=0.18, size=47*30, f=[0,60]Hz'
filename_parameters = '1Ch_complex_f_{}_{}_t_all_size_47x30.png'.format(fmin,fmax)
CNN_filters = '/CNN_filters_2_{}_{}_'.format(filter1,filter2)

ep_max = 110
ep = np.arange(1,ep_max)

fig, (ax1,ax2,ax3) = plt.subplots(1,3,figsize=(13,4))
# ax = plt.subplot(111)

if NN == 'LR':
    my_suptitle = fig.suptitle('LR - ' + parameters, fontsize=15,y=1.05)
elif NN == 'MLP':
    my_suptitle = fig.suptitle('MLP - ' + parameters, fontsize=15,y=1.05)
elif NN == 'MLPd':
    my_suptitle = fig.suptitle('MLP deeper - ' + parameters, fontsize=15,y=1.05)
elif NN == 'CNN':
    my_suptitle = fig.suptitle('CNN (4x8) filters - ' + parameters, fontsize=15,y=1.05)
elif NN == 'CNNd':
    my_suptitle = fig.suptitle('CNN deeper (2x4x8) filters - ' + parameters, fontsize=15,y=1.05)

ax1.plot(ep[:ep_max],train_losses[1:ep_max],'r^--',linewidth=2,label = 'Train loss')
ax1.set_xlabel('epochs',fontsize=12)
ax1.set_ylabel('Loss',fontsize=13)
ax1.set_title('Train loss',fontsize=16)
ax1.legend()
ax1.grid(True)

ax2.plot(ep[:ep_max],test_losses[1:ep_max],'go--',linewidth=2,label = 'Test loss')
ax2.set_xlabel('epochs',fontsize=12)
ax2.set_title('Test loss',fontsize=16)
ax2.legend()
ax2.grid(True)

ax3.plot(ep[:ep_max],acc_list[1:ep_max],'bo--',linewidth=2,label = 'Accuracy')
ax3.set_xlabel('epochs',fontsize=12)
ax3.set_title('Accuracy',fontsize=16)
ax3.legend()
ax3.grid(True)


plt.show()

if NN == 'LR':
    fig.savefig(dir_data +'/Ch_{}'.format(Ch) + dir_frequency + directory + '/LR_{}'.format(filename_parameters),bbox_inches='tight',bbox_extra_artists=[my_suptitle])
elif NN == 'MLP':
    fig.savefig(dir_data + '/Ch_{}'.format(Ch) + dir_frequency + directory + '/MLP_{}'.format(filename_parameters),bbox_inches='tight',bbox_extra_artists=[my_suptitle])
elif NN == 'MLPd':
    fig.savefig(dir_data + '/Ch_{}'.format(Ch) + dir_frequency + directory + '/MLP_deeper_{}'.format(filename_parameters),bbox_inches='tight',bbox_extra_artists=[my_suptitle])
elif NN == 'CNN':
    fig.savefig(dir_data + '/Ch_{}'.format(Ch) + dir_frequency + directory + CNN_filters +filename_parameters,bbox_inches='tight',bbox_extra_artists=[my_suptitle])
elif NN == 'CNNd':
    fig.savefig(dir_data + '/Ch_{}'.format(Ch) + dir_frequency + directory + CNN_filters +filename_parameters,bbox_inches='tight',bbox_extra_artists=[my_suptitle])


plt.close(fig)



model


#%%
# =============================================================================
#  FILTERS CNN
# =============================================================================
filter1 = 2
filter2 = 4
filter3 = 8
dir_frequency = 'frequency_0_60'
dir_filters = '/filters_2_4_8'
dir_tapers = '/tapers_1_2'
# filter3 = 4
Extent = [0 , x_size, fmin , fmax]

for i in range(filter1):
    fig, ax = plt.subplots()
    ax.set_title('Filter {} - conv layer 1'.format(i+1),fontsize=14)
    img1 = ax.imshow(torch.detach(conv_x1[1,i,:,:]).cpu().numpy().transpose(),origin='lower')
    fig.colorbar(img1, ax=ax,orientation="horizontal")
    ax1.set_aspect('auto')
    plt.show()
    fig.savefig('Plots/Ch_{}/random_N_015_W_25_dn_018/'.format(Ch)+dir_frequency + dir_tapers + dir_filters +'/CNN_100rand_f_{}_{}_Filter_{}_conv1_2x{}x{}_filters_size_47_30.png'.format(fmin,fmax,i+1,filter1,filter2),bbox_inches='tight')
    plt.close(fig)
   
    
for i in range(filter2):
    fig, ax = plt.subplots()
    ax.set_title('Filter {} - conv layer 2'.format(i+1),fontsize=14)
    img1 = ax.imshow(torch.detach(conv_x2[1,i,:,:]).cpu().numpy().transpose(),origin='lower')
    fig.colorbar(img1, ax=ax,orientation="horizontal")
    ax1.set_aspect('auto')
    plt.show()
    
    fig.savefig('Plots/Ch_{}/random_N_015_W_25_dn_018/'.format(Ch)+ dir_frequency + dir_tapers + dir_filters +'/CNN_100rand_f_{}_{}_Filter_{}_conv2_2x{}x{}_filters_size_47_30.png'.format(fmin,fmax,i+1,filter1,filter2),bbox_inches='tight')
    plt.close(fig)
    
    
for i in range(filter3):
    fig, ax = plt.subplots()
    ax.set_title('Filter {} - conv layer 3'.format(i+1),fontsize=14)
    img1 = ax.imshow(torch.detach(conv_x3[1,i,:,:]).cpu().numpy().transpose(),origin='lower')
    fig.colorbar(img1, ax=ax,orientation="horizontal")
    ax1.set_aspect('auto')
    plt.show()
    
    fig.savefig('Plots/Ch_{}/random_N_015_W_25_dn_018/'.format(Ch) + dir_frequency + dir_tapers + dir_filters +'/CNN_100rand_f_{}_{}_Filter_{}_conv3_2x{}x{}_filters_size_47_30.png'.format(fmin,fmax,i+1,filter1,filter2),bbox_inches='tight')
    plt.close(fig)


#%%
# =============================================================================
# # Weights for MLP
# =============================================================================

w = model.fc2.weight.view(20,10)
w = w.detach().cpu()

fig = plt.figure()
ax = plt.axes()
ax.set_xlabel('time',fontsize=13)
ax.set_ylabel('frequency',fontsize=12)
# Extent = [0 , 47, 0 , 30]
# ax.set_title('Weights - Linear Regression - Ch = {}, L2= 0.15'.format(Ch),fontsize=14)
ax.set_title('Weights - MLP, 1Ch, 100 rand, f=[10,40]Hz'.format(Ch),fontsize=14)
plt.imshow(w.numpy().transpose(),origin='lower')

# plt.gca().invert_yaxis()
# plt.grid(True)
plt.show()



#%%
# =============================================================================
# # Weights for linear regression
# =============================================================================

size_Re = X_train.shape[1]*X_train.shape[2]

w1 = model.fc1.weight[0,0:size_Re].view(X_train.shape[1],X_train.shape[2])
w1 = w1.detach().cpu()

w2 = model.fc1.weight[0,size_Re:size_Re*2].view(X_train.shape[1],X_train.shape[2])
w2 = w2.detach().cpu()

fig = plt.figure()
ax = plt.axes()
ax.set_xlabel('time',fontsize=13)
ax.set_ylabel('frequency',fontsize=12)
Extent = [0 , 47, 0 , 30]
# ax.set_title('Weights - Linear Regression - Ch = {}, L2= 0.15'.format(Ch),fontsize=14)
ax.set_title('Weights -Linear Regression, 1Ch, 100 rand, f=[10,30]Hz'.format(Ch),fontsize=14)
plt.imshow(w2.numpy().transpose(),origin='lower',extent=Extent)

# plt.gca().invert_yaxis()
# plt.grid(True)
plt.show()


# fig.savefig('Plots/Ch_{}/random_N_015_W_15_dn_018/'.format(Ch)+dir_frequency+'weights_LR_1Ch_100_rand_f_{}_{}_orig.png'.format(fmin,fmax),bbox_inches='tight',bbox_extra_artists=[my_suptitle])
# # fig.savefig('Plots/NW_46_30/weights_LR_1Ch_100rand_f_10_30_NW_46_30.png',bbox_inches='tight')
# plt.close(fig)





