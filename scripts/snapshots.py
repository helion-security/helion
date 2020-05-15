import json
import argparse
import os 

######################################## TUTORIAL ################################################################
# This script allows save snapshots based from the prediction file.
# The input to this script is the directory that contains predictions made using helion_predictions.py script
# The output is saved in the results folder as printed out after the successful execution of the script.

# Usage:
# python snapshots.py ../results/helion.train-helion/3gram  ../results/

################################################################################################################


def main(input_directory,snapshot_directory,tokens_directory):
    for root, dirs, files in os.walk(input_directory):
        # Get all files in the input directory
        for file in files:
            # Currently we take tsv files. Feel free to remove this.
            if file.endswith(".tsv"):
                filename = os.path.join(root, file)
                # Retrieve  Just the filename
                _, tail = os.path.split(filename)
                output_filename = snapshot_directory + tail
                just_token_output_filename = tokens_directory + tail

                # Create Directories if they dont' already exist
                snapshot_foldername = os.path.dirname(output_filename) 
                if not os.path.exists(snapshot_foldername):
                    os.makedirs(snapshot_foldername)
                    
                txt_foldername = os.path.dirname(just_token_output_filename) 
                if not os.path.exists(txt_foldername):
                    os.makedirs(txt_foldername)

                # For each file with predictions..
                with open(filename,'r') as fromFile:
                    for line_count, line in enumerate(fromFile,0):
                        
                        # Create a snapshot state model
                        state_model = {}
                        # We treat the input and predictions as a sequence of events.
                        tokens = line.replace('\t',',').replace('[','').replace(']','').split(', ')
                        
                        # We are using line number to refer back to the predictions
                        suff= '_sc_' + str(line_count)

                        for c_token, token_string in enumerate(tokens):
                            # We're appending to the same file
                            with open(just_token_output_filename.replace('.tsv',suff),'a') as txt_file:
                                token_string = token_string.replace('\'','')
                                # Handling multiple events in the same token
                                devices = token_string.split(',')[0].replace("<","").split('-')
                                if (token_string != "<s>" and token_string != "</s>"):
                                    if(len(token_string.split(',')) <=1):
                                        continue

                                    capabilities = token_string.split(',')[1].split('-')
                                    variable = token_string.split(',')[2].replace(">","").split('-')
                                    # If multiple events, loop over the tokens
                                    if (len(devices) >= 1):
                                        for count,dev in enumerate(devices):
                                            txt_file.write('<'+devices[count] + ',' + capabilities[count] + ',' + variable[count].replace('\n','')+ '>\n')
                                            # Update if the device capability has an event
                                            if(dev in state_model):
                                                state_model[dev][capabilities[count]] = variable[count].replace('\n','')                                        
                                            else:
                                                # Add state to the state model
                                                state_model[dev] = {}
                                                state_model[dev][capabilities[count]] = variable[count].replace('\n','')
                                    else:
                                        print("Something went wrong! Empty token..")
                                else:
                                    if(token_string == '<s>'):
                                        start_day = {}
                                        state_model['Start_Day'] = {}
                                    else:
                                        end_day = {}
                                        state_model['End_Day'] ={}
                                # sc and event is used to refer to snapshot count and the event in the state model resp.
                                suffix = '_sc_' + str(line_count) + '_event_' +str(c_token) + '.json'
                                # Dump the snapshot to respective json files.
                                with open(output_filename.replace('.tsv',suffix),'w') as toFile:
                                    json.dump(state_model,toFile)
            
    print("Done! Find the snapshots at: " + snapshot_directory   )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('input_directory', help='Input Folder containing helion scenario files in tsv.')    
    parser.add_argument('output_directory', help='Output folder where snapshots and prediction tokens are stored.')    
    
    args = parser.parse_args()
    input_directory = args.input_directory
    snapshot_directory = args.output_directory + '/snapshots/'
    tokens_directory = args.output_directory + '/tokens/'
    main(input_directory,snapshot_directory,tokens_directory)