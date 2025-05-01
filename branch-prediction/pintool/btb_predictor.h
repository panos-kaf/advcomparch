#ifndef BTB_H
#define BTB_H

#include "branch_predictor.h"

// Fill in the BTB implementation ...
class BTBPredictor : public BranchPredictor
{
public:
	BTBPredictor(int btb_lines, int btb_assoc)
	     : table_lines(btb_lines), table_assoc(btb_assoc), correct_target_predictions(0)
	{
		sets = btb_lines / btb_assoc;
		replacement_index = new int[sets]();

		BTB = new BTB_entry*[sets];
		for (int i = 0; i < sets; i++){			// init BTB
			BTB[i] = new BTB_entry[table_assoc];
			memset(BTB[i], 0, table_assoc * sizeof(BTB_entry));		
		}
	}

	~BTBPredictor() {
		for (int i = 0; i < sets; i++)
			delete[] BTB[i];
		delete[] BTB;
		delete[] replacement_index;
	}

    virtual bool predict(ADDRINT ip, ADDRINT target) {
		int set_index = ip % sets;
		
		for (int i = 0; i < table_assoc; i++){
			BTB_entry* entry = &BTB[set_index][i];
			if (entry->lookup_addr == ip)
				return entry->taken;
		}
		return false;
	}

    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
		int set_index = ip % sets;
		int i = 0;
		int empty_entry = 0;
		int repl_index = replacement_index[set_index];
		bool found = false;
		bool found_empty_entry = false;

		for (i = 0; i < table_assoc; i++){
			BTB_entry* entry = &BTB[set_index][i];
			if (entry->lookup_addr == ip){
				found = true;
				break;
			}
			else if (entry->lookup_addr == 0 && !found_empty_entry){
				found_empty_entry = true;
				empty_entry = i;
			}
		}
		if (found){
			if (!actual) {
				memset(&BTB[set_index][i], 0, sizeof(BTB_entry));
			}
			else {
				if (BTB[set_index][i].prediction == target) correct_target_predictions++;
			}
			updateCounters(predicted, actual);	// check for target misprediction
		}
		else{
			if (actual){
				BTB_entry new_entry;
				new_entry.lookup_addr = ip;
				new_entry.prediction = target;
				new_entry.taken = true;
				updateCounters(0, 1);		// miss if branch taken and not in BTB
				if (found_empty_entry)
					BTB[set_index][empty_entry] = new_entry;
				else{
					//fifo replacement strategy
					BTB[set_index][repl_index] = new_entry;
					replacement_index[set_index] = (repl_index + 1) % table_assoc;
				}
			}
			else updateCounters(0,0);		// if not taken and not in btb, hit
		}
	}

    virtual string getName() { 
        std::ostringstream stream;
		stream << "BTB-" << table_lines << "-" << table_assoc;
		return stream.str();
	}

    UINT64 getNumCorrectTargetPredictions() { 
		return correct_target_predictions;
	}

private:
	int table_lines, table_assoc, sets;
	typedef struct {
		unsigned long long lookup_addr, prediction;
		bool taken;
	} BTB_entry;

	BTB_entry** BTB;
	int *replacement_index;

	UINT64 correct_target_predictions;

};


#endif