conda info  |egrep -q "active environment.*ai4eusudoku" || conda activate ai4eusudoku
PYTHONPATH=src python -m ai4eu.orchestratorservice
