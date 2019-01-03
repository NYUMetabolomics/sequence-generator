#!/usr/bin/env python3
from collections import defaultdict
from itertools import count, chain, cycle, islice
from random import shuffle
import csv
import os
from argparse_prompt import PromptParser


class Trays:
    def __init__(self, start_num, end_num, trays = 'RGB', rows = 'ABCDE',columns = range(1,9), starting_location='GA1', blank_location = None, standard_location = None):
        self.start_num = start_num
        self.end_num = end_num
        self.trays = trays
        self.columns = columns
        self.rows = rows
        self.slots = [ t + r + str(c) for t in trays for r in rows for c in columns]
        self.vials = ['S{:05d}'.format(i) for i in range(start_num, end_num + 1) ]
        self.starting_index = self.slots.index(starting_location)
        self.blank_location = blank_location if blank_location is not None else self.slots[self.starting_index + len(self.vials)]
        self.standard_location = standard_location if standard_location is not None else self.slots[self.starting_index + len(self.vials) + 1]
        if len(self.slots) < len(self.vials) + self.starting_index: # TODO: do we need room for standard and blank vials?
            raise ValueError(f"Cannot fit {len(self.vials)} vials in {len(trays)} trays of {len(rows)}*{len(columns)}")
        if len(self.vials) < 1:
            raise ValueError("Please specify positive number of vials")
        if self.blank_location in self.slots[self.starting_index:self.starting_index + len(self.vials)]:
            raise ValueError("vial placement range includes blank located at {blank_location}!")
        if self.standard_location in self.slots[self.starting_index:self.starting_index + len(self.vials)]:
            raise ValueError("vial placement range includes standard vial located at {standard_location}!")

    @property
    def placement(self):
        return zip(self.vials,self.slots[self.starting_index:])
    
    @property
    def shuffled_placement(self):
        try:
            return self._shuffled
        except:
            self._shuffled = list(self.placement)
            shuffle(self._shuffled)
            return self._shuffled

    def print_placement(self):
        lookup = defaultdict(lambda: '      ', {slot: vial for vial, slot in self.placement})
##        x=[]
##        y=[]
##        z=[]
        for t in self.trays:
            print(f'\nTray {t}')
##            x.append(f'\nTray {t}')
            print('  '+'|'.join([str(c) for c in self.columns]))
##            y.append('  '+'|'.join([str(c) for c in self.columns]))
            for r in self.rows:
                print(r + ': ' + '|'.join([lookup[t + r + str(c)] for c in self.columns])+'\n')
##                z.append(r + ': ' + '|'.join([lookup[t + r + str(c)] for c in self.columns])+'\n')
'''            fname='mapping.txt'
            with open(fname, 'w',) as f:
                f.write(str(x))
                f.write(str(y))
                f.write(str(z))'''

class SequenceGenerator():
    def __init__(self, trays, sequence_number, control_block_interval, standard_str = 'ISTD', beginning_blanks = 1, control_block = 'BSB', end_with_control=True):
        placement = iter(trays.shuffled_placement)
        blanks = ([f"SQ{sequence_number}_B_{i}",trays.blank_location] for i in count())
        standards = ([f"SQ{sequence_number}_{standard_str}_{i}",trays.standard_location] for i in count())
        seq = []
        seq.extend(islice(blanks,beginning_blanks))
        def next_control_block():
            return [next({'B':blanks, 'S':standards}[c]) for c in control_block]
        while True:
            try:
                p=next(placement)
                seq.extend(chain(next_control_block(),[p],islice(placement,control_block_interval-1)))
            except StopIteration:
                if end_with_control:
                    seq.extend(next_control_block())
                break
        self.sequence = seq
    

    def directory(self, directory):
        if os.path.exists(directory)==True:
            print('That Sequence already has a folder in the directory in question. Would you like to continue?..')
            yn = ['y', 'n']
            ch = input('Type y or n...')
            while ch not in yn:
                ch = input('Please type y or n!...')
            if ch=='n':
                print ('Goodbye')
                exit()
            elif ch=='y':
                os.chdir(directory)
        else:
            os.makedirs(directory)
            os.chdir(directory)

    
    def export_format_1(self, filename):  #MSFILE
        with open(filename,'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['Bracket Type=4','Steve']) #Header
            writer.writerow(['File Name',''])
            writer.writerows(self.sequence)
        import pandas as pd
        df = pd.read_csv(filename)
        df.drop('Steve', axis=1,inplace=True)
        df.to_csv(filename, index=False)
        
    def export_format_2(self, filename):  #LCFILE
        with open(filename,'w',newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerows(self.sequence)
def main():
    parser = PromptParser()
    parser.add_argument('--sequence_number',help='Enter Sequence Number', type=int,default=None)
    parser.add_argument('--start_num',help='Enter first number in sequence', type=int, default=1)
    parser.add_argument('--end_num',help='Enter last number in sequence',type=int, default=None)
    parser.add_argument('--block_interval',help='After how many samples would you like a control block',type=int,default=None)
    parser.add_argument('--beginning_blanks',help='How many blanks would you like at the top of the run',type=int, default=1)
    parser.add_argument('--standard_format',help='Is this a pHILIC, lipid, or ZIC run (input 1, 2, or 3)', type=int, default=None)
    parser.add_argument('--directory',help='Enter directory to save files',  default='C:\\Users\\ASHL01\\Desktop')
    parser.add_argument('--filename1',help='Enter filename1 (LC)', default='SQtestLC.csv')
    parser.add_argument('--filename2',help='Enter filename2 (MS)', default='SQtestMS.csv')
    #print(parser.parse_args().argument)
    args = parser.parse_args()
    trays = Trays(args.start_num, args.end_num)
    trays.print_placement()
    standard_string = 'ISTD' if args.standard_format == 1 else 'LQC' if args.standard_format == 2 else 'QC' if args.standard_format==3 else None
    if standard_string is None:
        raise ValueError('enter 1 for pHILIC, 2 for lipid, or 3 for ZIC')
    seqgen = SequenceGenerator(trays, args.sequence_number, args.block_interval, standard_string, args.beginning_blanks)
    seqgen.directory(args.directory)
    if os.path.exists('.\\'+args.filename1):
        raise ValueError('This file already exists')
    if os.path.exists('.\\'+args.filename2):
        raise ValueError('This file already exists')
    seqgen.export_format_1(args.filename2)
    seqgen.export_format_2(args.filename1)

if __name__ == "__main__":
    main()
