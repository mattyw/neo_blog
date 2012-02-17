from flask import Flask
from flask import request, render_template, redirect, url_for
from py2neo import neo4j
import uuid
import os
app = Flask(__name__)

if os.environ.get('NEO4J_REST_URL'):
    gdb_url = urlparse(os.environ.get('NEO4J_REST_URL'))    
    gdb = neo4j.GraphDatabaseService('http://{host}:{port}{path}'.format(host=graph_db_url.hostname, port=graph_db_url.port, path=graph_db_url.path), user_name=graph_db_url.username, password=graph_db_url.password)
else:
    gdb_url = 'http://localhost:7474/db/data'
    gdb = neo4j.GraphDatabaseService(gdb_url)

ref_node = gdb.get_reference_node()


@app.route('/style.css')
def css():
    return redirect(url_for("static", filename="style.css"))

def get_node_by_id(post_id):
    for node in ref_node.get_related_nodes("outgoing", "post"):
        if node['post_id'] == post_id:
            return node

@app.route('/newpost', methods=['POST'])
def new_post():
    if request.method == 'POST':
        post_id = str(uuid.uuid1())
        node = gdb.create_node({"title": request.form['title'],
                                "content": request.form['content'],
                                "post_id": post_id})
        ref_node.create_relationship_to(node, "post")
    return redirect(url_for('view'))

@app.route('/')
def view():
    posts = []
    all_nodes = ref_node.get_related_nodes("outgoing", "post")
    for node in all_nodes:
        posts.append({'title': node['title'],
                      'content': node['content'],
                      'post_id': node['post_id'],
                      'connections': node.get_related_nodes("all", "similar")})
    posts.reverse()
    return render_template("index.html", posts=posts, all=all_nodes)
        
@app.route('/<string:post_a_id>/relatesto/<string:post_b_id>')
def relates(post_a_id, post_b_id):
    node_a = None
    node_b = None
    for node in ref_node.get_related_nodes("outgoing", "post"):
        print node['post_id']
        if node['post_id'] == post_a_id:
            node_a = node
        if node['post_id'] == post_b_id:
            node_b = node
    if node_a and node_b:
        node_a.create_relationship_to(node_b, "similar", {})
    return redirect(url_for('view'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0')
