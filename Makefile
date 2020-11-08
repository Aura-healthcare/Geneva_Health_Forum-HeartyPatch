streamlit:
	streamlit run GEH_EP/app_streamlit.py 

streamlit_live:
	streamlit run GEH_EP/app_streamlit_live.py

clean_results:
	rm  data/results/*

streamlit_server:
	python GEH_EP/modules/sockets_utilities.py --server

streamlit_client:
	python GEH_EP/modules/sockets_utilities.py --client