#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 16 09:19:24 2018

@author: jimmy
"""

import torch
import numpy as np


class S2VT(torch.nn.Module):
    def __init__(self, input_dim, batch, encoder_unit, decoder_unit,
                 encoder_layer, decoder_layer, one_hot):
        super(S2VT, self).__init__()
        #Need to add embedding size
        self.one_hot_size = one_hot
        self.batch_size = batch
        self.input_size = input_dim
        self.output_size = decoder_unit
        #To change between encoding & decoding
        self.encoder_stage = True
        self.decoder_stage = False
        
        #left to implement attention and schedule sampling
        #Need to change this ratio by model.schedule_sample_rate 
        self.schedule_sample_rate = 1
        
        self.attention_vector = None
        
        #save after encoding
        self.encoding_code = None
        self.encoding_c = None
        self.encoder_h_size = encoder_unit
        self.decoder_h = None
        self.decoder_c = None
        self.decoder_h_size = decoder_unit
        ################
        #Can change initialize
        ################
        
        # shape = (num_layer, batch, hidden_size)
        self.encoder_h0 = torch.zeros((encoder_layer, batch, self.encoder_h_size),
                                      dtype = torch.float32)
        
        self.encoder_c0 = torch.zeros((encoder_layer, batch, self.encoder_h_size),
                                      dtype = torch.float32)
        self.encoder = torch.nn.LSTM(input_size = input_dim,
                                     hidden_size = encoder_unit,
                                     num_layers = encoder_layer,
                                     dropout = 0)
        
        self.decoder_input_size = (decoder_unit + encoder_unit)
        ################
        #Can change initialize
        #shape : (num_layer, batch, hidden_size)
        ################
        self.input_embedding = torch.nn.Linear(self.one_hot_size, self.decoder_h_size)
        self.output_embedding = torch.nn.Linear(self.decoder_h_size, self.one_hot_size)

        self.decoder_h0 = torch.zeros((decoder_layer, batch, self.decoder_h_size),
                                      dtype = torch.float32)
        self.decoder_c0 = torch.zeros((decoder_layer, batch, self.decoder_h_size),
                                      dtype = torch.float32)
        
        self.decoder = torch.nn.LSTM(input_size = self.decoder_input_size,
                                     hidden_size = decoder_unit,
                                     num_layers = decoder_layer,
                                     dropout = 0)
    def forward(self, input_data, correct_answer):
        #correct_answer : whole sequence of answer
        #input_data shape: (sequence_len, batch, input_size)
        #output_data shape: (sequence_len, batch, input_size)
        if self.encoder_stage:
            print("Encoding")
            encoder_output, (encoder_h_n, encoder_c_n) = self.encoder(input_data, (self.encoder_h0, self.encoder_c0))
            self.encoding_code = encoder_h_n
            self.encoding_c = encoder_c_n
            
            padding_tag = torch.zeros((len(input_data), self.batch_size, self.decoder_h_size), 
                                      dtype= torch.float32)
            
            decoder_input = torch.cat( (encoder_output, padding_tag), dim = 2)
            
            decoder_output, (decoder_h_n, decoder_c_n) = self.decoder(decoder_input, (self.decoder_h0, self.decoder_c0))
            self.decoder_h = decoder_h_n
            self.decoder_c = decoder_c_n
            return encoder_output
        
        elif self.decoder_stage:
            print("Decoding")
            encoder_output, (encoder_h_n, encoder_c_n) = self.encoder(input_data, (self.encoding_code, self.encoding_c))
            
            ###############
            #to add bos tag
            #shape : (1, batch_size, feature)
            ###############
            bos_tag = torch.zeros((1, self.batch_size, self.one_hot_size), 
                                      dtype= torch.float32) 
            
            temp_h = None
            temp_c = None
            
            First_flag = True
            decoder_output = []
            decoder_output_words = []
            #######################
            #When training : decoder will run len(answer) times
            #Because "encoder_output" contains len(answer) sequence.
            #(We will input POS tags of len(answer) )
            #When testing : set Maxlen to restrict the len of output 
            #######################
            for time in range(len(encoder_output)):
                if First_flag:
                    one_time = encoder_output[time]
                    bos_embedding = self.input_embedding(bos_tag)
                    one_time = one_time.reshape((1, self.batch_size, -1)) #-1 -> hidden_size
                    
                    decoder_input = torch.cat((one_time, bos_embedding), dim = 2)
                    
                    output, (h, c) = self.decoder(decoder_input, (self.decoder_h, self.decoder_c))
                    temp_h = h
                    temp_c = c
                    ###########################
                    #Can do something to output
                    ###########################
                    
                    word = self.output_embedding(output)
                    decoder_output.append(output)
                    decoder_output_words.append(word)
                    First_flag = False
                else:
                    one_time = encoder_output[time]
                    one_time = one_time.reshape((1, self.batch_size, -1))
                    to_concat = None
                    if np.random.random() < self.schedule_sample_rate:
                        to_concat = correct_answer[time]
                        to_concat = to_concat.reshape((1, self.batch_size, -1))
                        to_concat = self.input_embedding(to_concat)
                    else:
                        to_concat = decoder_output[-1]
                    
                    decoder_input = torch.cat((one_time, to_concat), dim = 2)
                    output, (h, c) = self.decoder(decoder_input, (temp_h, temp_c))
                    temp_h = h
                    temp_c = c
                    ###########################
                    #Can do something to output
                    ###########################
                    word = self.output_embedding(output)
                    decoder_output.append(output)
                    decoder_output_words.append(word)
            return decoder_output_words
    
test_input = [ torch.Tensor(np.random.randn(10,1,4096)) for i in range(5)]
test_pad = [torch.Tensor(np.zeros( (10,1,4096) )) for i in range(5)]
test_ans = [torch.Tensor(np.zeros( (10,1,10) )) for i in range(5)]
test = S2VT(4096, 1, 256, 256, 1, 1, 10)            
encode = test(test_input[0], test_ans[0])
test.encoder_stage = False
test.decoder_stage = True
ans = test(test_input[1], test_ans[0])
print(ans)
            
