#ifndef BRANCH_PREDICTOR_H
#define BRANCH_PREDICTOR_H

#include <sstream> // std::ostringstream
#include <cmath>   // pow(), floor
#include <cstring> // memset()

/**
 * A generic BranchPredictor base class.
 * All predictors can be subclasses with overloaded predict() and update()
 * methods.
 **/
class BranchPredictor
{
public:
    BranchPredictor() : correct_predictions(0), incorrect_predictions(0) {};
    ~BranchPredictor() {};

    virtual bool predict(ADDRINT ip, ADDRINT target) = 0;
    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) = 0;
    virtual string getName() = 0;

    UINT64 getNumCorrectPredictions() { return correct_predictions; }
    UINT64 getNumIncorrectPredictions() { return incorrect_predictions; }

   void resetCounters() { correct_predictions = incorrect_predictions = 0; };

protected:
    void updateCounters(bool predicted, bool actual) {
        if (predicted == actual)
            correct_predictions++;
        else
            incorrect_predictions++;
    };

private:
    UINT64 correct_predictions;
    UINT64 incorrect_predictions;
};

class NbitPredictor : public BranchPredictor
{
public:
    NbitPredictor(unsigned index_bits_, unsigned cntr_bits_, int fsm_ = 1)
        : BranchPredictor(), index_bits(index_bits_), cntr_bits(cntr_bits_), fsm(fsm_) {
        table_entries = 1 << index_bits;
        TABLE = new unsigned long long[table_entries];
        memset(TABLE, 0, table_entries * sizeof(*TABLE));
        
        COUNTER_MAX = (1 << cntr_bits) - 1;
    };
    ~NbitPredictor() { delete TABLE; };

    virtual bool predict(ADDRINT ip, ADDRINT target) {
        unsigned int ip_table_index = ip % table_entries;
        unsigned long long ip_table_value = TABLE[ip_table_index];
        unsigned long long prediction = ip_table_value >> (cntr_bits - 1);
        return (prediction != 0);
    };

    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
        unsigned int ip_table_index = ip % table_entries;
        switch (fsm){
			case 1:		// saturated counter (default)
				if (actual) {
					if (TABLE[ip_table_index] < COUNTER_MAX)
					TABLE[ip_table_index]++;
				} else {
					if (TABLE[ip_table_index] > 0)
					TABLE[ip_table_index]--;
				}
				break;

			case 2:
				if (actual) {
					if (TABLE[ip_table_index] < COUNTER_MAX)
						TABLE[ip_table_index]++;
				}
				else {
					if (TABLE[ip_table_index] == COUNTER_MAX)
						TABLE[ip_table_index]--;
					else{
						TABLE[ip_table_index] = 0;
					}
				}
				break;

			case 3:
				if (actual){
					if (TABLE[ip_table_index] == 0)
						TABLE[ip_table_index]++;
					else if( TABLE[ip_table_index] < COUNTER_MAX)
						TABLE[ip_table_index] = COUNTER_MAX;
				}
				else {
					if (TABLE[ip_table_index] > 0)
						TABLE[ip_table_index]--;
				}
				break;

			case 4:
				if (actual){
					if (TABLE[ip_table_index] == 0)
						TABLE[ip_table_index]++;
				else TABLE[ip_table_index] = COUNTER_MAX;
				}
				else {
					if (TABLE[ip_table_index] == COUNTER_MAX)
						TABLE[ip_table_index]--;
					else TABLE[ip_table_index] = 0;
				}
				break;

			case 5:
				if (actual){
					if (TABLE[ip_table_index] == 0)
						TABLE[ip_table_index]++;
					else if (TABLE[ip_table_index] == COUNTER_MAX)
						TABLE[ip_table_index]--;
					else 
						TABLE[ip_table_index] = COUNTER_MAX;
				}
				else {
					if (TABLE[ip_table_index] != 0)
						TABLE[ip_table_index]--; 
				}
				break;
			default:
				std::cout<<"Invalid FSM!\n";
	}
        updateCounters(predicted, actual);
    };

    virtual string getName() {
        std::ostringstream stream;
        stream << "Nbit-" << pow(2.0,double(index_bits)) / 1024.0 << "K-" << cntr_bits;
        return stream.str();
    }

private:
    unsigned int index_bits, cntr_bits;
    unsigned int COUNTER_MAX;
	int fsm;

 /* Make this unsigned long long so as to support big numbers of cntr_bits. */
    unsigned long long *TABLE;
    unsigned int table_entries;
};

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
			delete BTB[i];
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
				updateCounters(0, 1);				// direction miss if not in BTB 
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
