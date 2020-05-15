import subprocess
import json
import argparse
import sys
import os 


######################################## TUTORIAL ################################################################
# This script allows prediction using Helion.
# The input to this script is training file, vocab file, order and scenarios file.
# The output is saved in the results folder which contains a tab separated values for input scenario and predictions.
# You can configure it to select different prediction length, flavors, and models.

# Usage:
# python3 helion_predictions.py ../data/generated_data/validation/scenarios_from_evaluators/ev1-scenarios.txt  ../data/generated_data/training/training_model/helion.train -o 3 -v ../data/generated_data/training/training_model/helion.vocab 

# Simple Usage of brain server:
# 1. Run Helion server with: 
# braind ../data/helion.train.txt ../data/helion.vocab 
# 2. Make request with:
# cat request > /tmp/fifo0 && cat /tmp/fifo1
################################################################################################################

# Directory to save predictions to
OUTPUT_DIR = '../results/'

# NUmber of Predictions
PREDICTION_LENGTH = 10

# Model Algorithm ; alternative is backoff
MODEL = 'interpolate'
# Model Flavors
FLAVORS = ['up','down']

def construct_model(flavor,history):
    conf_json = {}
    conf_json["model"] = MODEL
    conf_json["flavor"] = flavor
    conf_json["history"] = history
    conf_json["length"] =  PREDICTION_LENGTH
    with open('request', 'w') as outfile:
        json.dump(conf_json, outfile)

def run_server(t,n,v):
    cmd1 = 'braind ' + t + ' '  + v + ' --order ' + str(n)  
    print("Command: ",cmd1)
    subprocess.check_output(cmd1,  shell = True)

def repeated_tokens(tokens_list):
    prev_pred = ''
    for t in tokens_list:
        if(prev_pred == ''):
            prev_pred = t
        else:
            if(t==prev_pred):
                return True
            else:
                prev_pred = t
    return False
def make_request():
    
    cmd = 'cat request > /tmp/fifo0'
    subprocess.check_output(cmd,  shell = True)
    
    cmd1 = 'cat /tmp/fifo1' 
    binary_object = subprocess.check_output(cmd1,  shell = True)

    output_json = {}
    try:
        output_json = json.loads(binary_object.decode("utf-8"))
    except ValueError:
        print("JSON Decode Error: ", binary_object)
        return
    
    # If the token is repeated make another request to the server.
    if (repeated_tokens(output_json["stream"])):
        print("Made a recursive call because the prediction had repeated tokens")
        make_request()

    return output_json

def kill_server():
    #Get process ID if braind is running
    cmd = 'ps aux | grep -v  grep | grep braind | awk \'{print $2;}\' | cut -d \' \' -f 1'
    cmd_result = subprocess.check_output(cmd,  shell = True)
    pid = cmd_result.decode("utf-8").strip()

    kill_cmd = 'kill -9 ' + pid  
    subprocess.check_output(kill_cmd,  shell = True)

def create_directory(training_filem,vocab_file,order):
    # Directory where output is saved. 
    final_path= OUTPUT_DIR + os.path.basename(training_file).replace('.txt','') + '-' + os.path.basename(vocab_file).replace('.vocab','')  + '/' + str(order) + 'gram/'

    # REMOVE the folder everytime. The training results will always be saved to the same folder.
    cmd1 = 'rm -rf ' +final_path
    subprocess.check_output(cmd1,  shell = True)

    # Make output directory if it doesn't exist
    if not os.path.exists(final_path):
        os.makedirs(final_path)
        print("Created respective directories.. ")
    
    return final_path



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Provide the directory from which sequence of tokens need to be generated.')
    parser.add_argument('scenarios_file', type=argparse.FileType('r'))
    parser.add_argument('training_file', type=argparse.FileType('r'))
    parser.add_argument('-o', '--order', type=int, default=3)
    parser.add_argument('-v', '--vocab', type=argparse.FileType('r'))
    
    args = parser.parse_args()
    order = args.order
    if args.order < 2:
        sys.stderr.write('ERROR: [-o ORDER] must be an integer greater than one.\n')
        sys.exit(1)

    input_file = args.scenarios_file.name
    training_file = args.training_file.name
    vocab_file = args.vocab.name

    print("Start.......")
    
    output_path = create_directory(training_file,vocab_file,order)
    for flavor in FLAVORS:
        

        with open(output_path + flavor + '.tsv','w') as toFile:
            with open(input_file,'r',encoding="utf-8-sig") as fromFile:
                for line in fromFile:
                    history = line.split()
                    
                    # Create Input
                    construct_model(flavor,history)    

                    # Train the model
                    run_server(training_file,order,vocab_file)

                    # Construct INPUT FOR MODEL
                    output_json = make_request()

                    kill_server()
                    
                    to_write = str(history) + '\t' + str(output_json["stream"]) + '\n'
                    toFile.write(to_write)

    print()
    print("Output Written to Path: ", OUTPUT_DIR)

            
