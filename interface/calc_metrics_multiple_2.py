import gym
import scipy.special
import ipdb
import sys
import json
import random
import numpy as np
import cProfile
import pdb
import timeit
import json
import os
import argparse
import glob
# home_path = '/Users/xavierpuig/Desktop/MultiAgentBench/'
home_path = os.getcwd()
home_path = '/'.join(home_path.split('/')[:-2])

sys.path.append(home_path+'/vh_mdp')
sys.path.append(home_path+'/virtualhome')
sys.path.append(home_path+'/vh_multiagent_models')

import utils
from simulation.evolving_graph.utils import load_graph_dict
from profilehooks import profile
import pickle
import pdb


# Options, should go as argparse arguments
agent_type = 'MCTS' # PG/MCTS
simulator_type = 'unity' # unity/python
dataset_path = '../dataset_toy4/init_envs/'


def get_metrics(alice_results, test_results, episode_ids):
    # if len(alice_results.keys()) != len(test_results.keys()):
    #     print(alice_results.keys())
    #     print(test_results.keys())
    #     print('different numbers of episodes:', len(alice_results.keys()), len(test_results.keys()))
    #     # return 0, 0, 0
    mS = []
    mL = []
    mSwS = []
    for seed in range(5):
        Ls = []
        Ss = []
        SWSs = []
        alice_S = []
        alice_L = []

        for episode_id in episode_ids:
            if episode_id not in alice_results:
                S_A, L_A = 0, 250
                pdb.set_trace()
                # continue
            else:
                if alice_results[episode_id]['S'][seed] == '':
                    continue

                S_A = alice_results[episode_id]['S'][seed]
                L_A = alice_results[episode_id]['L'][seed]
            if episode_id not in test_results:
                S_B, L_B = 0, 250
                # pdb.set_trace()
                # continue
            else:
                try:
                    if test_results[episode_id]['S'][seed] == '':
                        continue

                    S_B = test_results[episode_id]['S'][seed]
                    L_B = test_results[episode_id]['L'][seed]
                except:
                    pdb.set_trace()
                # if S_B < 0.6:
                #     pdb.set_trace()
            alice_S.append(S_A)
            alice_L.append(L_A)
            Ls.append(L_B)
            Ss.append(S_B)
            SWSs.append(0 if S_B < 1 else max(L_A / L_B - 1.0, 0))
            if SWSs[-1] == 0:
                print(episode_id, seed)
            if S_A > 0 and SWSs[-1] > 1.:
                pass
                # pdb.set_trace()
                # print(episode_id)
        # print('Alice:', np.mean(alice_S), np.mean(alice_L))
        # print('Alice:', np.mean(alice_S), '({})'.format(np.std(alice_S)), np.mean(alice_L), '({})'.format(np.std(alice_L)))
        # print('Bob:', np.mean(Ss), '({})'.format(np.std(Ss)), np.mean(Ls), '({})'.format(np.std(Ls)), np.mean(SWSs), '({})'.format(np.std(SWSs)))
        mS.append(np.mean(Ss))
        mL.append(np.mean(Ls))
        mSwS.append(np.mean(SWSs))

    return np.mean(mS), np.mean(mL), np.mean(mSwS), np.std(mS), np.std(mL),  np.std(mSwS)


parser = argparse.ArgumentParser()
parser.add_argument('--seed', type=int, default=123, help='Random seed')
parser.add_argument('--max-episode-length', type=int, default=200, help='Maximum episode length')
parser.add_argument('--agent-type', type=str, default='MCTS', help='Alice type: MCTS (default), PG')
parser.add_argument('--simulator-type', type=str, default='unity', help='Simulator type: python (default), unity')
# parser.add_argument('--dataset-path', type=str, default='../initial_environments/data/init_envs/init7_100_simple.p', help='Dataset path')
# parser.add_argument('--record-dir', type=str, default='../record/init7_100_same_room_simple', help='Record directory')
parser.add_argument('--recording', action='store_true', default=False, help='True - recording frames')
parser.add_argument('--num-per-apartment', type=int, default=10, help='Maximum #episodes/apartment')
parser.add_argument('--task', type=str, default='setup_table', help='Task name')
parser.add_argument('--mode', type=str, default='simple', help='Task name')
parser.add_argument('--port', type=int, default=8095, help='port')
parser.add_argument('--display', type=str, default='2', help='display')
parser.add_argument('--use-editor', action='store_true', default=False, help='Use unity editor')
parser.add_argument('--num-per-task', type=int, default=30, help='Maximum #episodes/taks')


if __name__ == '__main__':
    args = parser.parse_args()
    print (' ' * 26 + 'Options')
    for k, v in vars(args).items():
            print(' ' * 26 + k + ': ' + str(v))
    env_task_set = pickle.load(open(home_path+'/data_challenge//test_env_set_help_20_neurips.pik', 'rb'))
    # env_task_set = pickle.load(open(home_path+'/vh_multiagent_models/initial_environments/data/init_envs/train_demo_set.pik', 'rb'))
    
    args.record_dir_alice = '../record_scratch/rec_good_test/multiAlice_env_task_set_20_check_neurips_test'
    print(args.record_dir_alice + '/results_{}.pik'.format(1))
    alice_results = pickle.load(open(args.record_dir_alice + '/results_{}.pik'.format(0), 'rb'))

    # args.record_dir = '../record/init7_Bob_test_set_{}'.format(args.num_per_task)
    record_dirs = [
     '../record_scratch/rec_good_test/multiBob_env_task_set_20_randomgoal',
     '../record_scratch/rec_good_test/multiBob_env_task_set_20_predgoal',
     '../record_scratch/rec_good_test/multiBob_env_task_set_20_check_neurips_test_recursive',
        '../record_scratch/rec_good_test/multiBob_env_task_set_20_check_neurips_RL_MCTS',
     '../record_scratch/rec_good_test/multiAlice_env_task_set_20_check_neurips_test'
    ]

    # args.record_dir = './record_scratch/rec_good_test/Alice_env_task_set_20_check_neurips_test'
    # args.record_dir = './record_scratch/rec_good_test/Bob_env_task_set_20_check_neurips_test_recursive'
    task_names = ['setup_table', 'put_fridge', 'prepare_food', 'put_dishwasher', 'read_book']
    final_results = {'S': {}, 'SWS': {}, 'L': {}, 'classes': task_names}
    for record_dir in record_dirs:
        test_results = pickle.load(open(record_dir + '/results_{}.pkl'.format('redo'), 'rb'))
        method_name = record_dir.split('_')[-1]
        final_results['S'][method_name] = [], []
        final_results['SWS'][method_name] = [], []
        final_results['L'][method_name] = [], []
        num_agents = 1

        episode_ids = list(range(len(env_task_set)))
        S = [0] * len(episode_ids)
        L = [200] * len(episode_ids)
        SRO, ALO, SWSO, stdRO, stdLO, stdSO = get_metrics(alice_results, test_results, episode_ids)
        print('overall:', SRO, ALO, SWSO)



        sr_list, al_list, sws_list = [], [], []
        for task_name in task_names:
            episode_ids_task = [episode_id for episode_id in episode_ids if env_task_set[episode_id]['task_name'] == task_name]
            SR, AL, SWS, stdR, stdL, stdS = get_metrics(alice_results, test_results, episode_ids_task)
            sr_list.append(str(SR))
            al_list.append(str(AL))
            sws_list.append(str(SWS))

            final_results['S'][method_name][0].append(SR)
            final_results['SWS'][method_name][0].append(SWS)
            final_results['L'][method_name][0].append(AL)
            final_results['S'][method_name][1].append(stdR)
            final_results['SWS'][method_name][1].append(stdS)
            final_results['L'][method_name][1].append(stdL)



            print('{}:'.format(task_name), SR, AL, SWS)
        final_results['S'][method_name][0].append(SRO)
        final_results['SWS'][method_name][0].append(SWSO)
        final_results['L'][method_name][0].append(ALO)
        final_results['S'][method_name][1].append(stdRO)
        final_results['SWS'][method_name][1].append(stdSO)
        final_results['L'][method_name][1].append(stdLO)

        sr_list.append(str(SRO))
        al_list.append(str(ALO))
        sws_list.append(str(SWSO))

        print("SR")
        print(','.join(sr_list))
        print("AL")
        print(','.join(al_list))
        print("SWS")
        print(','.join(sws_list))
    with open('results_mcts_across_seeds.json', 'w+') as f:
        f.write(json.dumps(final_results))