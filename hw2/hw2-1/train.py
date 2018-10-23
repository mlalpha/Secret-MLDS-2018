
import S2VT
import readin_raw as read
import torch
import numpy as np


## S2VT bos_tag 
## S2VT padding_tag to cuda()

### training data ###
test_input = [ torch.Tensor(np.random.randn(10,1,4096)) for i in range(5)]
test_pad = [torch.Tensor(np.zeros( (10,1,4096) )) for i in range(5)]
test_ans = [torch.Tensor(np.zeros( (10,1,10) )) for i in range(5)]
test_correct_answer = [torch.ones((10,1,1), dtype=torch.long) for i in range(5)]



batch_size = 64
dataloader, one_hot_size, answer_len = read.generate_dataloader(batch_size = batch_size)

input_size = 4096
encoder_hidden = 256
decoder_hidden = 256
encoder_layer = 1
decoder_layer = 1
output_dim = one_hot_size


learning_rate = 0.001
training_epoch = 200
cuda_avilabel = True
# we can change the schedule sampling rate by parameter lamda; the first 100 epochs set the rate to 1
lamda = 0.98

# we can get a 's2vt.plk' file which contains the model for restoring after we call training()
def training(input_size,batch_size,encoder_hidden,decoder_hidden,encoder_layer,decoder_layer,output_dim,cuda_avilabel,lamda,training_data):
	model = S2VT(input_size,batch_size,encoder_hidden,decoder_hidden,encoder_layer,decoder_layer,output_dim)
	if(cuda_avilabel):
		model = model.cuda()
	print(model)
	optimizer = torch.optim.Adam(model.parameters(),lr = learning_rate)
	criterion = torch.nn.CrossEntropyLoss()
	loss_array = []

	for epoch in range(training_epoch):
	    for x,y,z in training_data:
	        model.encoder_stage = True
	        model.decoder_stage = False
	        encoder_input = x  # the input to encoder during encoding stage
	        correct_answer = y   # correct answer 
	        encoder_pad = torch.zeros((correct_answer[0],correct_answer[1],input_size),dtype = torch.float)       # the input to encoder during decoding stage
	        _, target = correct_answer.max(dim=2)  # not one-hot, but a number imply the right class
	        if(cuda_avilabel):
	        	encoder_input = encoder_input.cuda()
	        	correct_answer = correct_answer.cuda()
	        	encoder_pad = encoder_pad.cuda()
	        	target = target.cuda()
	        # target = test_correct_answer[iteration] # not one-hot, but a number imply the right class
	        encoded = model(encoder_input,correct_answer) # correct_answer is just a parameter but not used during encoding stage
	        # eocoded can be used for attention
	        model.encoder_stage = False
	        model.decoder_stage = True
	        output = model(encoder_pad,correct_answer)
	        print(output[0].shape)
	        output_tmp = torch.cat((output),0)
	        print(output_tmp.shape)
	        output = output_tmp.view(-1,output_dim)
	        print(output.shape)
	        target = target.view(-1)
	        loss = criterion(output,target)
	        print(loss.item())
	        loss_array.append(loss.item())
	        
	        optimizer.zero_grad()
	        loss.backward()
	        optimizer.step()
	        
	    # we can change the schedule sampling rate by parameter lamda; the first 100 epochs set the rate to 1
	    if epoch >= 100:
	        tmp_rate = model.schedule_sample_rate
	        model.schedule_sample_rate = lamda * tmp_rate
	### save model ###
	torch.save(model,'s2vt.pkl')
	return loss_array

def restore_model(model_name):
	### restore model ###
	net = torch.load(model_name)
	print(net)
	return net

history = training(input_size=input_size, batch_size=batch_size, encoder_hidden=encoder_hidden,
                   decoder_hidden=decoder_hidden, encoder_layer=encoder_layer, decoder_layer=decoder_layer,
                   output_dim=one_hot_size, cuda_avilabel=True, lamda=lamda,training_data=dataloader)
#model_name = 's2vt.pkl'
#restored_net = restore_model(model_name)









