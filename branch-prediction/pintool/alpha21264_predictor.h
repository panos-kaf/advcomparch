#ifndef ALPHA21264_PREDICTOR_H
#define ALPHA21264_PREDICTOR_H

#include "branch_predictor.h"
#include "global_history_predictor.h"
#include "local_history_predictor.h"

class Alpha21264Predictor : public BranchPredictor {
	public:
		Alpha21264Predictor()
			: BranchPredictor(),
			  local(new LocalHistoryPredictor(10, 10, 10, 3)), // BHT: 1K 10-bit, PHT: 1K 3-bit
			  global(new GlobalHistoryPredictor(12, 12, 2))    // PHT: 4K 2-bit
		{
			META_SIZE = 1 << 12;	// 4K entries
			meta = new unsigned int [META_SIZE];
		}
	
		~Alpha21264Predictor() {
			delete local;
			delete global;
		}
	
		bool predict(ADDRINT ip, ADDRINT target) override {
			unsigned int meta_index = ip % META_SIZE;
			unsigned int counter = meta[meta_index];
			bool use_global = (counter >> 1) != 0;
	
			bool prediction = use_global ? global->predict(ip, target) : local->predict(ip, target);
			last_prediction = prediction;
			last_actual = false; // updated in `update`
			last_index = meta_index;
			return prediction;
		}
	
		void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) override {
			last_actual = actual;
	
			bool local_pred = local->predict(ip, target);
			bool global_pred = global->predict(ip, target);
	
			// Update the meta predictor
			if (local_pred != global_pred) {
				if (global_pred == actual) {
					if (meta[last_index] < 3) meta[last_index]++;
				} else {
					if (meta[last_index] > 0) meta[last_index]--;
				}
			}
	
			local->update(local_pred, actual, ip, target);
			global->update(global_pred, actual, ip, target);
			updateCounters(last_prediction, actual);
		}
	
		std::string getName() override {
			return "Alpha21264Hybrid";
		}
	
	private:
		unsigned int *meta;
		unsigned int META_SIZE;
	
		LocalHistoryPredictor *local;
		GlobalHistoryPredictor *global;
	
		bool last_prediction, last_actual;
		unsigned int last_index;
	};
	
#endif