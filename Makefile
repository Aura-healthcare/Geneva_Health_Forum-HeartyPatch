FOLDER_PATH= .

run:
	. $(FOLDER_PATH)/env/bin/activate; \
	streamlit run GEH_EP/app_streamlit_live.py \

hp_stream:
	python GEH_EP/modules/tcp_script.py

# Utilities

install:
	\
	python3 -m venv env; \
	. $(FOLDER_PATH)/env/bin/activate; \
	pip install -r requirements.txt;\

streamlit_server:
	python GEH_EP/modules/sockets_utilities.py --server

streamlit_client:
	python GEH_EP/modules/sockets_utilities.py --client

clean_results:
	rm  data/results/*

streamlit_simulation:
	. $(FOLDER_PATH)/env/bin/activate; \
	streamlit run GEH_EP/app_streamlit_simulation.py \ 

