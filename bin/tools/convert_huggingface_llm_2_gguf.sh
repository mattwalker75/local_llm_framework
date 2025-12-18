#!/bin/bash
########################################################
#
#  This converts a HuggingFace LLM ( with .safetensor files ) to
#  a GGUF format that is needed to get the LLM to run locally
#  from the Llama server
#
#  Simple test if model converted successfully:
#   ../../../llama.cpp/llama \
#  -m ../../models/test_gguf/Qwen3-30B-q4_K_M.gguf \
#  -p "Write a Python hello world"
#
########################################################

CONVERT="../../../llama.cpp/convert_hf_to_gguf.py"

HUGGING_FACE_MODEL="../../models/Qwen--Qwen3-Coder-30B-A3B-Instruct"

OUTPUT_GGUF_MODEL="../../models/test_gguf/Qwen--Qwen3-Coder-30B-A3B-Instruct.gguf"

OUTTYPE="f16"


QUANTIZER="../../../llama.cpp/build/bin/llama-quantize"

OUTPUT_QUANTIZED_MODEL="../../models/test_gguf/Qwen--Qwen3-Coder-30B-A3B-Instruct-q4_K_M.gguf"

QUANT_TYPE="q4_K_M"

#
#  Convert HuggingFace LLM to GGUF format for Llama server
#
echo "Converting the HuggingFace LLM to GGUF format"
python ${CONVERT} ${HUGGING_FACE_MODEL} --outfile ${OUTPUT_GGUF_MODEL} --outtype ${OUTTYPE}
if (( $? != 0 ))
then
   echo "Error converting the model"
   exit 1
fi
echo "Successfully converted the model"

#
#  Quantize the converted LLM
#
echo "Quantizing the GGUF formatted LLM"
${QUANTIZER} ${OUTPUT_GGUF_MODEL} ${OUTPUT_QUANTIZED_MODEL} ${QUANT_TYPE}
if (( $? != 0 ))
then
   echo "Error quantizing the model"
   exit 1
fi
echo "Successfully quantiziing the model"

