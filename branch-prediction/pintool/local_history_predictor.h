#ifndef LOCAL_HISTORY_PREDICTOR_H
#define LOCAL_HISTORY_PREDICTOR_H

#include "branch_predictor.h"


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

#endif