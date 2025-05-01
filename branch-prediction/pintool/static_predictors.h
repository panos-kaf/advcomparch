#ifndef STATIC_PREDICTORS_H
#define STATIC_PREDICTORS_H

#include "branch_predictor.h"

class AlwaysTakenPredictor: public BranchPredictor{
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


#endif