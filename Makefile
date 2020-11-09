streamlit_live:
	streamlit run GEH_EP/app_streamlit_live.py

hp_stream:
	python GEH_EP/modules/tcp_script.py

# Utilitiess

streamlit_server:
	python GEH_EP/modules/sockets_utilities.py --server

streamlit_client:
	python GEH_EP/modules/sockets_utilities.py --client


clean_results:
	rm  data/results/*

streamlit:
	streamlit run GEH_EP/app_streamlit.py 
