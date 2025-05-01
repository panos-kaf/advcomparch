#ifndef TOURNAMENT_PREDICTOR_H
#define TOURNAMENT_PREDICTOR_H

#include "branch_predictor.h"

	
class TournamentPredictor : public BranchPredictor {
    public:
        TournamentPredictor(BranchPredictor* P0, BranchPredictor* P1, unsigned chooser_bits)
            : predictor0(P0), predictor1(P1)
        {
            chooser_size = 1 << chooser_bits;
            chooser_max = 3;  // Assuming a 2-bit saturating counter
            chooser_table = new unsigned int[chooser_size]();
            chooser_mask = chooser_size - 1;
        }
    
        ~TournamentPredictor() {
            delete[] chooser_table;
        }
    
        virtual bool predict(ADDRINT ip, ADDRINT target) override {
            bool pred0 = predictor0->predict(ip, target);
            bool pred1 = predictor1->predict(ip, target);
    
            unsigned chooser_index = ip & chooser_mask;
            bool use_pred1 = chooser_table[chooser_index] >> 1;
    
            last_ip = ip;
            last_pred0 = pred0;
            last_pred1 = pred1;
    
            return use_pred1 ? pred1 : pred0;
        }
    
        virtual void update(bool predicted, bool actual, ADDRINT ip, ADDRINT target) override {
            predictor0->update(last_pred0, actual, ip, target);
            predictor1->update(last_pred1, actual, ip, target);
    
            if (last_pred0 != last_pred1) {
                unsigned chooser_index = last_ip & chooser_mask;
                if (last_pred1 == actual && chooser_table[chooser_index] < chooser_max)
                    chooser_table[chooser_index]++;
                else if (last_pred0 == actual && chooser_table[chooser_index] > 0)
                    chooser_table[chooser_index]--;
            }
    
            updateCounters(predicted, actual);
        }
    
        virtual string getName() override {
            std::ostringstream stream;
            stream << "Tournament-" << chooser_size << "-entries-"
                    << predictor0->getName() << "-vs-" << predictor1->getName();
            return stream.str();
        }
    
    private:
        BranchPredictor* predictor0;
        BranchPredictor* predictor1;
    
        unsigned int* chooser_table;
        unsigned int chooser_size;
        unsigned int chooser_max;
        unsigned int chooser_mask;
    
        // For update logic
        ADDRINT last_ip;
        bool last_pred0;
        bool last_pred1;
    };
    

#endif