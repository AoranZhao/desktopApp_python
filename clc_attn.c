//
//  clc_attn.c
//  TestCL
//
//  Created by BrainCo on 12/13/15.
//  Copyright © 2015 BrainCo. All rights reserved.
//



#define sqr(x) ((x)*(x))

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "fft.h"

int clc_attn(
             const double *input_eeg, //
             int input_size, //300
             double low_alpha, // 5
             double high_alpha, // 8
             double low_beta, // 8
             double high_beta, // 20
             int sample_rate) // 60
{
    int low_alpha_i,high_alpha_i, low_beta_i, high_beta_i;
    double alpha=0, beta = 0;
    int result;
    double * output_frequency_Re = malloc(input_size * sizeof(double));
    memcpy(output_frequency_Re,input_eeg,input_size*sizeof(double));
    double * const a zero_imag = malloc(input_size * sizeof(double));
    double * temp = zero_imag;
    int i;
    for(i=0;i<input_size;i++)
    {
        *(temp++) = 0.0;
    }
    transform(output_frequency_Re, zero_imag, input_size);
    
    // calc corresponding frequency index
    low_alpha_i = round(low_alpha * input_size / sample_rate);
    high_alpha_i = round(high_alpha * input_size / sample_rate);
    low_beta_i = round(low_beta * input_size / sample_rate);
    high_beta_i = round(high_beta * input_size / sample_rate);
    
    for(i=low_alpha_i; i<=high_alpha_i; i++)
    {
        alpha += (sqr(output_frequency_Re[i])+sqr(zero_imag[i]));
        
#ifdef _Debug_Alpha
        printf("[calculated alpha]: freq: %d, %f + i %f  Ref: %f + i %f \n",i,output_frequency_Re[i],zero_imag[i],output_frequency_Re[input_size-i],zero_imag[input_size-i]);
#endif
    }
    
    for (i=low_beta_i; i<=high_beta_i;i++)
    {
        beta += (sqr(output_frequency_Re[i])+sqr(zero_imag[i]));
        
#ifdef _Debug_Alpha
        printf("[calculated beta]: freq: %d, %f + i %f\n",i,output_frequency_Re[i],zero_imag[i]);
#endif
    }
    
#ifdef _Debug_Alpha
    printf("[calculated alpha_beta]: %f, %f\n",alpha,beta);
#endif
    
    alpha /= high_alpha_i - low_alpha_i + 1;
    beta /= high_beta_i - low_beta_i + 1;
    
#ifdef _Debug_Alpha
    printf("[calculated alpha_beta]: %f, %f\n",alpha,beta);
#endif
    result = round((100 * beta / alpha));
    
    return result;
}
