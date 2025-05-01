#ifndef GLOBAL_HISTORY_PREDICTOR_H
#define GLOBAL_HISTORY_PREDICTOR_H

#include "branch_predictor.h"

class GlobalHistoryPredictor : public BranchPredictor {
	public:
		GlobalHistoryPredictor(unsigned bhr_bits_, unsigned pht_bits_, unsigned cntr_bits_)
			: BranchPredictor(),
			  bhr_bits(bhr_bits_), pht_bits(pht_bits_), cntr_bits(cntr_bits_), BHR(0)
		{
			pht_size = 1 << pht_bits;
			COUNTER_MAX = (1 << cntr_bits) - 1;
	
			PHT = new unsigned int[pht_size];
			memset(PHT, 0, sizeof(unsigned int) * pht_size);
		}
	
		~GlobalHistoryPredictor() {
			delete[] PHT;
		}
	
		virtual bool predict(ADDRINT ip, ADDRINT target) {
			unsigned int index = BHR & ((1 << pht_bits) - 1);
			unsigned int counter = PHT[index];
			return (counter >> (cntr_bits - 1)) != 0;
		}
	
		virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
			unsigned int index = BHR & ((1 << pht_bits) - 1);
	
			if (actual) {
				if (PHT[index] < COUNTER_MAX)
					PHT[index]++;
			} else {
				if (PHT[index] > 0)
					PHT[index]--;
			}
	
			BHR = BHR << 1;					//shift bhr
			BHR |= actual;					//place result in lsb
			BHR &= ((1 << bhr_bits) - 1);	//remove last entry
	
			updateCounters(predicted, actual);
		}
	
		virtual string getName() {
			std::ostringstream stream;
			stream << "GlobalHistory-BHR" << bhr_bits
				   << "-PHT" << (1 << pht_bits)
				   << "-Counter" << cntr_bits << "b";
			return stream.str();
		}
	
	private:
		unsigned int bhr_bits, pht_bits, cntr_bits;
		unsigned int COUNTER_MAX;
	
		unsigned int BHR;
		unsigned int *PHT;
		unsigned int pht_size;
	};	

#endif