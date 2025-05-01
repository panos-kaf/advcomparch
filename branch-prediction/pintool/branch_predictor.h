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
		if (fsm == 1)
			stream << "Nbit-" << pow(2.0,double(index_bits)) / 1024.0 << "K-" << cntr_bits << "-Saturated_Counter";
        else
			stream << "Nbit-" << pow(2.0,double(index_bits)) / 1024.0 << "K-" << cntr_bits << "-FSM-" << fsm;
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

class AlwaysTakenPredictor: public BranchPredictor
{
public:
	AlwaysTakenPredictor() {};
	~AlwaysTakenPredictor() {};

	virtual bool predict(ADDRINT ip, ADDRINT target){ return true; }
	
	virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target){
		updateCounters(predicted, actual);
	}

	virtual string getName() { return "Static-AlwaysTaken"; }
};

class BTFNTPredictor: public BranchPredictor
{
public:
	BTFNTPredictor() {};
	~BTFNTPredictor() {};

	virtual bool predict(ADDRINT ip, ADDRINT target){ return ip > target; }
	
	virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target){
		updateCounters(predicted, actual);
	}

	virtual string getName() { return "Static-BT-FNT"; };
};

class LocalHistoryPredictor : public BranchPredictor
{
public:
    LocalHistoryPredictor(int bht_bits_, int history_length_, int pht_bits_, int cntr_bits_)
        : BranchPredictor(),
          bht_bits(bht_bits_),
          history_length(history_length_),
          pht_bits(pht_bits_),
          cntr_bits(cntr_bits_)
    {
        BHT_size = 1 << bht_bits;
        PHT_size = 1 << pht_bits;

        BHT = new unsigned int[BHT_size];
        PHT = new unsigned int[PHT_size];

        memset(BHT, 0, sizeof(unsigned int) * BHT_size);
        memset(PHT, 0, sizeof(unsigned int) * PHT_size);

        COUNTER_MAX = (1 << cntr_bits) - 1;
    }

    ~LocalHistoryPredictor() {
        delete[] BHT;
        delete[] PHT;
    }

    virtual bool predict(ADDRINT ip, ADDRINT target) {
        int bht_index = ip % BHT_size;
        int history = BHT[bht_index];
        int pht_index = history % PHT_size;

        unsigned int counter = PHT[pht_index];
        return (counter >> (cntr_bits - 1)) != 0;
    }

    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
        int bht_index = ip % BHT_size;
        int history = BHT[bht_index];
        int pht_index = history % PHT_size;

        // Update saturating counter
        if (actual) {
            if (PHT[pht_index] < COUNTER_MAX)
                PHT[pht_index]++;
        } else {
            if (PHT[pht_index] > 0)
                PHT[pht_index]--;
        }

        // Update local history (shift in actual outcome)
        BHT[bht_index] = ((history << 1) | (actual ? 1 : 0)) & ((1 << history_length) - 1);

        updateCounters(predicted, actual);
    }

    virtual string getName() {
        std::ostringstream stream;
        stream << "LocalHistory-BHT" << BHT_size
               << "-PHT" << PHT_size
               << "-History" << history_length
               << "-Counters" << cntr_bits;
        return stream.str();
    }

private:
    int bht_bits, history_length, pht_bits, cntr_bits;
    int BHT_size, PHT_size;
    unsigned int COUNTER_MAX;

    unsigned int *BHT;  // Per-branch local history
    unsigned int *PHT;  // Saturating counters indexed by local history
};


class GlobalHistoryPredictor : public BranchPredictor
{
public:
    GlobalHistoryPredictor(unsigned history_bits_, unsigned cntr_bits_): 
	BranchPredictor(), history_bits(history_bits_), cntr_bits(cntr_bits_), GHR(0)
    {
        pht_size = 1 << history_bits;
        COUNTER_MAX = (1 << cntr_bits) - 1;

        PHT = new unsigned int[pht_size];
        memset(PHT, 0, sizeof(unsigned int) * pht_size);
    }

    ~GlobalHistoryPredictor() { delete[] PHT; }

    virtual bool predict(ADDRINT ip, ADDRINT target) {
        unsigned int counter = PHT[GHR]; 	// use GHR to index PHT
        return (counter >> (cntr_bits - 1)) != 0;
    }

    virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) {
        unsigned int index = GHR;

		if (actual) {
            if (PHT[index] < COUNTER_MAX)
                PHT[index]++;
        } else {
            if (PHT[index] > 0)
                PHT[index]--;
        }
		
		GHR = GHR << 1;
		if (actual) GHR |= 1;
		GHR &= (1 << history_bits) - 1;	// keep GHR within history_bits

        updateCounters(predicted, actual);
    }

    virtual string getName() {
        std::ostringstream stream;
        stream << "GlobalHistory-" << history_bits << "-bit-" << cntr_bits << "-counter";
        return stream.str();
    }

private:
    unsigned int history_bits, cntr_bits;
    unsigned int COUNTER_MAX;

    unsigned int GHR;
    unsigned int *PHT;
    unsigned int pht_size;
};

class TournamentPredictor : public BranchPredictor {
	public:
		TournamentPredictor(LocalHistoryPredictor* local, GlobalHistoryPredictor* global, unsigned chooser_bits)
			: BranchPredictor(), localPredictor(local), globalPredictor(global)
		{
			chooser_size = 1 << chooser_bits;
			chooser_max = 3;
			chooser_table = new unsigned int[chooser_size]();
			chooser_mask = chooser_size - 1;
		}
	
		~TournamentPredictor() {
			delete[] chooser_table;
		}
	
		virtual bool predict(ADDRINT ip, ADDRINT target) override {
			bool local_pred = localPredictor->predict(ip, target);
			bool global_pred = globalPredictor->predict(ip, target);
	
			unsigned chooser_index = ip & chooser_mask;
			bool use_global = chooser_table[chooser_index] >> 1;
	
			last_ip = ip;
			last_local_pred = local_pred;
			last_global_pred = global_pred;
	
			return use_global ? global_pred : local_pred;
		}
	
		virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) override {
			localPredictor->update(last_local_pred, actual, ip, target);
			globalPredictor->update(last_global_pred, actual, ip, target);
	
			// Update chooser only if predictions differ
			if (last_local_pred != last_global_pred) {
				unsigned chooser_index = last_ip & chooser_mask;
				if (last_global_pred == actual && chooser_table[chooser_index] < chooser_max)
					chooser_table[chooser_index]++;
				else if (last_local_pred == actual && chooser_table[chooser_index] > 0)
					chooser_table[chooser_index]--;
			}
	
			updateCounters(predicted, actual);
		}
	
		virtual string getName() override {
			std::ostringstream stream;
			stream << "Tournament-" << chooser_size <<"-entries-" << localPredictor->getName() << "-vs-" << globalPredictor->getName();
			return stream.str();
		}
	
	private:
		LocalHistoryPredictor* localPredictor;
		GlobalHistoryPredictor* globalPredictor;
	
		unsigned int* chooser_table;
		unsigned int chooser_size;
		unsigned int chooser_max;
		unsigned int chooser_mask;
	
		// For update logic
		ADDRINT last_ip;
		bool last_local_pred;
		bool last_global_pred;
	};

#endif
 
