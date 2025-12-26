#!/bin/bash
########################################################
#
#  This converts a HuggingFace LLM ( with .safetensor files ) to
#  a GGUF format that is needed to get the LLM to run locally
#  from the Llama server
#
########################################################

#
#  QUANT_TYPE   / MODEL SIZE   /  RAM NEEDED
#     f16          90-100 G        110 - 120 G
#     q8_0         45-50 G         55 - 50 G
#     q6_K         38-42 G         45 - 50 G <-- tight at 64G RAM
#     q5_K_M       30-34 G         36 - 40 G <-- best
#     q4_K_M       24-28 G         30 - 34 G <-- safe
#     q3_K_M       18-22 G         24 - 28 G
#
########################################################

#
#  EXTERNAL TOOLS
#

#  Convert HuggingFace LLM to GGUF format for Llama
CONVERT_TOOL="../../../llama.cpp/convert_hf_to_gguf.py"

#  Quantizing the GGUF converted LLM
QUANTIZER="../../../llama.cpp/build/bin/llama-quantize"

FORCE=0
MODEL_ROOT="../../models"
OUTTYPE="f16"
QUANT_TYPE="q5_K_M"

########################################################

#
#  Print out description of the tool
#
function description {
   echo ""
   echo "This script converts a HuggingFace LLM ( with .safetensor files ) to"
   echo "a GGUF format that is needed to get the LLM to run locally from the"
   echo "local Llama LLM server that supports OpenAI API interaction."
   echo ""
   echo "The HuggingFace LLM Model will need to already be downloaded and saved"
   echo "to the \"models\" directory.  The GGUF converted LLM will be saved in"
   echo "the \"models\" directory."
   echo ""
   echo "Simple test if model converted successfully:"
   echo "   ../../../llama.cpp/llama \  "
   echo "   -m ../../models/<GGUF model directory>/<model>.gguf \  "
   echo "   -p \"Write a Python hello world\""
   echo ""
}

#
#  Print out usage information
#
function usage {
   echo "Usage:  $0 -s <HuggingFace Model> -d <GGUF Model Name> [-f]"
   echo ""
   echo "   -s <HuggingFace Model> - This is the name of the downloaded HuggingFace"
   echo "                            that you want to convert to a GGUF Model"
   echo "   -d <GGUF Model Name> - This is the name that you want to give to the"
   echo "                          LLM model after it is convert to the GGUF format"
   echo "   -f   - Optionally delete the GGUF Model if it exists and rebuild it"
   echo ""
   echo " NOTE:  The models will be located in the \"models\" directory"
   echo ""
   echo "EXAMPLE:" 
   echo " $0 -f -s Qwen--Qwen2.5-Coder-7B-Instruct -d Qwen--Qwen2.5-Coder-7B-Instruct-GGUF"
   echo ""
   exit 255
}

########################################################

#  Get command line parms
while getopts "s:d:hf" opt
do
   case $opt in
      s) HF_MODEL=${OPTARG} ;; 
      d) GGUF_MODEL=${OPTARG} ;;
      f) FORCE=1 ;;
      h) description; usage ;; 
      *) usage ;;
   esac
done

#  Check that both parms are set
if [[ ${HF_MODEL} == "" ]] || [[ ${GGUF_MODEL} == "" ]]
then
   usage
fi

#  Verify the source HuggingFace model exists
if [[ ! -d "${MODEL_ROOT}/${HF_MODEL}" ]]
then
   echo "The source LLM model does not exist"
   echo "${MODEL_ROOT}/${HF_MODEL}"
   exit 255
fi

#  Verify the destination model doesn't exist
if [[ -d "${MODEL_ROOT}/${GGUF_MODEL}" ]]
then
   if (( $FORCE == 0 ))
   then
      echo "Looks like a model exists with that name already"
      echo "model location:  ${MODEL_ROOT}/${GGUF_MODEL}"
      exit 255
   else
      rm -Rf ${MODEL_ROOT}/${GGUF_MODEL}
      if (( $? != 0 ))
      then
         echo "Error deleting the old GGUF model"
         echo "model location:  ${MODEL_ROOT}/${GGUF_MODEL}"
         exit 1
      fi
   fi
fi

mkdir "${MODEL_ROOT}/${GGUF_MODEL}"
if (( $? != 0 ))
then
   echo "Error creating model directory"
   echo "model location:  ${MODEL_ROOT}/${GGUF_MODEL}"
   exit 1
fi

GGUF_MODEL_FILE=$(echo ${GGUF_MODEL} | sed 's/-[Gg][Gg][Uu][Ff]$//g')


#  Convert HuggingFace LLM to GGUF format for Llama server
echo "Converting the HuggingFace LLM to GGUF format"
python ${CONVERT_TOOL} ${MODEL_ROOT}/${HF_MODEL} --outfile ${MODEL_ROOT}/${GGUF_MODEL}/${GGUF_MODEL_FILE}_${OUTTYPE} --outtype ${OUTTYPE}
if (( $? != 0 ))
then
   echo "Error converting the model"
   exit 1
fi
echo "Successfully converted the model"


#  Quantize the converted LLM
echo "Quantizing the GGUF formatted LLM"
${QUANTIZER} ${MODEL_ROOT}/${GGUF_MODEL}/${GGUF_MODEL_FILE}_${OUTTYPE} ${MODEL_ROOT}/${GGUF_MODEL}/${GGUF_MODEL_FILE}_${OUTTYPE}_${QUANT_TYPE}.gguf ${QUANT_TYPE}
if (( $? != 0 ))
then
   echo "Error quantizing the model"
   exit 1
fi
echo "Successfully quantizing the model"


#  Perform cleanup tasks
rm -Rf ${MODEL_ROOT}/${GGUF_MODEL}/${GGUF_MODEL_FILE}_${OUTTYPE}
if (( $? != 0 ))
then
   echo "Error deleting un-quantized model"
   echo "${MODEL_ROOT}/${GGUF_MODEL}/${GGUF_MODEL_FILE}_${OUTTYPE}"
   exit 1
fi

