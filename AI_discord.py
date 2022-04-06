# things we need for NLP
import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

# things we need for Tensorflow
import numpy as np
import tflearn
import tensorflow as tf
import random
import pickle

# import our chat-bot intents file
import json

def setup(app):
    filename = 'intents_' + app + '.json'
    with open(filename) as file:
        data = json.load(file)

    # print(data)

    words = []
    labels = []
    docs = []
    docs_x = []
    docs_y = []
    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            wrds = nltk.word_tokenize(pattern)
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intent["tag"])

        if intent["tag"] not in labels:
            labels.append(intent["tag"])

    words = [stemmer.stem(w.lower()) for w in words if w != "?"]
    words = sorted(list(set(words)))

    labels = sorted(labels)

    training = []
    output = []

    out_empty = [0 for _ in range(len(labels)) ]

    for x,doc in enumerate(docs_x):
        bag = []
        wrds = [stemmer.stem(w.lower()) for w in doc]
        for w in words:
            if w in wrds:
                bag.append(1)
            else:
                bag.append(0)

        output_row = out_empty[:]
        output_row[labels.index(docs_y[x])] = 1

        training.append(bag)
        output.append(output_row)

    training = np.array(training)
    output = np.array(output)

        # with open("data.pickle","wb") as f:
        #     pickle.dump((words,labels,training,output),f)

    tf.compat.v1.reset_default_graph()

    net = tflearn.input_data(shape=[None,len(training[0])])
    net = tflearn.fully_connected(net,8)
    net = tflearn.fully_connected(net,8)
    net = tflearn.fully_connected(net, len(output[0]), activation = "softmax") # softmax activation
    net = tflearn.regression(net)

    model = tflearn.DNN(net)

    # try:
    #     model.load("model.tflearn")
    # except:
    model.fit(training,output,n_epoch = 1000, batch_size = 8,show_metric=True)
    #     model.save("model.tflearn")

    return model,words,labels,data


def bag_of_words(s,words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for se in s_words:
        for i,w in enumerate(words):
            if w == se:
                bag[i] = 1

    return np.array(bag)


def chat(inp,model,words,labels,data):    

    results = model.predict([bag_of_words(inp,words)])[0]
    # print(results)
    results_index = np.argmax(results)  ## pick the top one in the array
    tag = labels[results_index]
    # print(tag)

    if results[results_index] > 0.7:
        for tg in data["intents"]:
            if tg["tag"] == tag:
                responses = tg

        return (responses)
    else:
        return ("wrong")




   



