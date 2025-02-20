import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd

# Initialize session state variables
if 'filtered' not in st.session_state:
    st.session_state.filtered = False
if 'result' not in st.session_state:
    st.session_state.result = None
if 'commentaires' not in st.session_state:
    st.session_state.commentaires = ""
if 'anomalies' not in st.session_state:
    st.session_state.anomalies = False

# Write directly to the app
st.title("Gestion des anomalies de transport :truck:")
st.write(
    """
    L'objectif de cette application est de toper les anomalies de transports merci de remplir les 4 critères :

    - Filtre par numéro de commande
    - Filtre par code client
    - Filtre par date d'expédition
    - Filtre par date d'expédition réelle

"""
)

# Get the current credentials
session = get_active_session()

# Execute the SQL query to get distinct numero_commande values
distinct_numeros_commande = session.sql("SELECT DISTINCT numero_commande FROM anomalies_transport").collect()

# Extract the values from the query result
numeros_commande_list = [row['NUMERO_COMMANDE'] for row in distinct_numeros_commande]

# Add an empty option at the beginning of the list
numeros_commande_list.insert(0, "")

# Execute the SQL query to get distinct code_client values
distinct_code_client = session.sql("SELECT DISTINCT code_client FROM anomalies_transport").collect()

# Extract the values from the query result
code_client_list = [row['CODE_CLIENT'] for row in distinct_code_client]

# Add an empty option at the beginning of the list
code_client_list.insert(0, "")

# Create columns to align filters in a single row
col1, col2, col3, col4 = st.columns(4)

with col1:
    numero_commande = st.selectbox("Numéro de commande", options=numeros_commande_list)

with col2:
    code_client = st.selectbox('Code client', options=code_client_list)

with col3:
    date_exp = st.date_input("Date d'expédition")

with col4:
    date_exp_reelle = st.date_input("Date d'expédition (réelle)")

# Button to filter data
if st.button("Filtrer"):
    # Construct the SQL query based on the selected filters
    query = "SELECT * FROM anomalies_transport WHERE 1=1"
    if numero_commande:
        query += f" AND numero_commande = '{numero_commande}'"
    if code_client:
        query += f" AND code_client = '{code_client}'"
    if date_exp:
        query += f" AND date_exp = '{date_exp}'"
    if date_exp_reelle:
        query += f" AND date_exp_reelle = '{date_exp_reelle}'"

    # Execute the query
    result = session.sql(query).collect()

    # Store the result in session state
    st.session_state.result = result
    st.session_state.filtered = True

# Check if data has been filtered
if st.session_state.filtered:
    # Check if any data is returned
    if st.session_state.result:
        # Convert the result to a pandas DataFrame
        df = pd.DataFrame(st.session_state.result)
        # Display the DataFrame as a table
        st.table(df)

        # Check if only one row is returned
        if len(df) == 1:
            # Display comment area and buttons
            st.write("Veuillez ajouter un commentaire et signaler une anomalie si nécessaire.")
            st.session_state.commentaires = st.text_area("Commentaires", value=st.session_state.commentaires)
            st.session_state.anomalies = st.checkbox("Anomalie détectée", value=st.session_state.anomalies)

            if st.button("Confirmer ✅"):
                # Update the database with the new comment and anomaly status
                session.sql(f"""
                    UPDATE anomalies_transport
                    SET anomalies = {st.session_state.anomalies}, commentaires = '{st.session_state.commentaires}'
                    WHERE numero_commande = '{numero_commande}' AND anomalies <>
                """).collect()
                st.success("Données mises à jour avec succès !")

            if st.button("Annuler ❌"):
                st.warning("Action annulée.")
    else:
        # Display a warning message if no data is found
        st.warning("Aucune donnée trouvée pour les critères sélectionnés.")
