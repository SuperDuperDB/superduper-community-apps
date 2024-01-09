import streamlit as st
import hashlib

# Function to generate a hash of the password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize session state for authentication status
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None

# Replace with your own user credentials
USERNAME = 'admin'
PASSWORD = 'password'

# Hashed password
hashed_password = hash_password(PASSWORD)

# User input for authentication
input_username = st.sidebar.text_input("Username")
input_password = st.sidebar.text_input("Password", type="password")

# Check the username and password
if st.sidebar.button('Login'):
    if input_username == USERNAME and hashlib.sha256(input_password.encode()).hexdigest() == hashed_password:
        st.session_state['authentication_status'] = True
        st.sidebar.success('Logged in as {}'.format(input_username))
    else:
        st.session_state['authentication_status'] = False
        st.sidebar.error('Incorrect Username/Password')

# Display content if authenticated
if st.session_state['authentication_status']:
    import clip
    import PIL.Image
    import os

    import streamlit as st
    from superduperdb import superduper
    from superduperdb.backends.mongodb import Collection
    from superduperdb import Document
    from superduperdb import CFG
    from superduperdb.ext.pillow import pil_image

    import hashlib
    import streamlit as st

    CFG.cluster.backfill_batch_size = 5000

    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/ecommerce")

    @st.cache_resource
    def _init():
        return superduper(mongodb_uri, artifact_store='filesystem://./data/artifacts/', downloads_folder='./data/downloads')

    db = _init()


    collection = Collection('multimodal')


    st.title('Retail with SuperDuperDB')


    def _search(k, v, index, n=3):
        return db.execute(
            collection.like(Document({k: v}), vector_index=index, n=n).find({})
        )

    def text_2_image_search(text):
        return _search('search', text, 'my-index')

    def text_2_text_search(text):
        return _search('title', text, 'text-index', n=10)

    def image_search(img):
        return _search('img', pil_image(img), 'my-index')

    def random_product():
        return next(db.execute(
            collection.aggregate([
                {'$sample': {'size': 1 }}
            ])
        ))


    tab0, tab1, tab2, tab3 = st.tabs(["Data", "Text Search", "Image Search", "Browse"])

    with tab0:
        import json
        query = st.text_area(
            'Enter a MongoDB query',
            value='{}',
        )
        submit_button = st.button("Query", key='query-button')
        if submit_button:
            import pymongo
            collection = pymongo.MongoClient(mongodb_uri)['ecommerce']['multimodal']
            res = collection.find(json.loads(query), {'_id': 0}).limit(5)
            st.text(
                json.dumps([r for r in res], indent=2)
            )

    with tab1:
        query = st.text_input('---', placeholder='Search for something...')
        submit_button = st.button("Search")
        if submit_button:
            results = text_2_image_search(query)
            for r in results:
                r = r.unpack()
                st.image(r['img'], caption=r['title'])

    with tab2:
        uploaded_file = st.file_uploader("Upload an image of a product", key='image-search')
        if uploaded_file:
            image = PIL.Image.open(uploaded_file)
            results = image_search(image)
            for r in results:
                r = r.unpack()
                st.image(r['img'], caption=r['title'])

    with tab3:
        r = random_product().unpack()
        
        st.button('Refresh')

        col1, col2, col3 = st.columns(3)

        with col2:
            st.image(r['img'], caption=r['title'])

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('### Based on image')
            image_results = image_search(r['img'])
            for r in image_results:
                r = r.unpack()
                st.image(r['img'])

        with col2:
            st.markdown('### Based on title')
            text_results = text_2_text_search(r['title'])
            for r in text_results:
                r = r.unpack()
                st.text(r['title'])