#ifndef NBIT_PREDICTOR_H
#define NBIT_PREDICTOR_H

#include "branch_predictor.h"

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

#endif