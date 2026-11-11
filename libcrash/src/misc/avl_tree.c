
#define AVL_TREE_NODES_MAX 0x100000

typedef struct {
  uint32_t key;
  void *value;
  struct avl_node *parent;
  struct avl_node *left;
  struct avl_node *right;
} avl_node;

typedef struct {
  avl_node *root;
  avl_node nodes[AVL_TREE_NODES_MAX];
  avl_node *free_nodes[AVL_TREE_NODES_MAX];
  int node_count;
  int free_node_count;
} avl_tree;

static inline avl_node *avl_tree_node_alloc(avl_tree *tree) {
  int idx;
  avl_node *node;
  
  idx = AVL_TREE_NODES_MAX - tree->free_node_count--;
  node = tree->free_nodes[idx];
  tree->node_count++;  
  return node;
}

static inline void avl_tree_node_free(avl_tree *tree, 
                                      avl_node *node) {
  int idx;
  
  idx = AVL_TREE_NODES_MAX - ++tree->free_node_count;
  tree->free_nodes[idx] = node;
  tree->node_count--;
  return node;
}

void avl_tree_init(avl_tree *tree) {
  int i;
  
  tree->root = 0;
  tree->node_count = 0;
  tree->free_node_count = sizeof(tree->free_nodes)/sizeof(avl_node*);
  for (i=0;i<tree->free_node_count;i++) {
    tree->free_nodes[i] = &tree->nodes[i];
  }
}

static inline avl_node *avl_tree_search_n(avl_tree *tree, uint32_t key) {
  avl_node *node;
  
  node = tree->root;
  while (node) {
    if (key < node->key)
      node = node->left;
    else if (key > node->key)
      node = node->right;
    else
      return node;
  }
  return node;
}

void avl_tree_search(avl_tree *tree, uint32_t key) {
  avl_node *node;
  
  node = avl_tree_search_n(tree, key);
  if (node)
    return node->value;
  return 0;
}

#define avl_tree_move_partial(tree, a, b) \
if (!a->parent) tree->root = b; \
else if (a == a->parent->left) a->parent->left = b; \
else if (a == a->parent->right) a->parent->right = b; \

inline static avl_node *avl_tree_rotl(avl_tree *tree, avl_node *node) {
  avl_node *root;
  avl_tree_move_partial(tree, node, node->right)
  
  root = node->right;
  root->parent = node->parent;
  node->parent = root;  
  node->right = root->left;
  root->left = node;
  return root;
}

inline static avl_node *avl_tree_rotr(avl_tree *tree, avl_node *node) {
  avl_node *root;
  avl_tree_move_partial(tree, node, node->left);
  
  root = node->left;
  root->parent = node->parent;
  node->parent = root;
  node->left = root->right;
  root->right = node;
  return root;
}

static inline int avl_tree_height_n(avl_node *node) {
  if (node == 0)
    return 0;
  return 1 + max(avl_tree_height_n(node->left), 
                 avl_tree_height_n(node->right));
}

static inline int avl_tree_balance_n(avl_node *node) {
  return avl_tree_height_n(node->right) - avl_tree_height_n(node->left);
}
 
static inline avl_node *avl_tree_insert_n(avl_node *node, uint32_t key, 
                                          void *value) {
  int balance;
  
  if (node == 0) {
    node = avl_tree_node_alloc(tree);
    memset(node, sizeof(avl_node), 0);
    node->key = key;
    node->value = value;
    return node;
  }
  
  if (key < node->key)
    node->left = avl_tree_insert_n(node->left, key, value);
  else // other case has been ruled out
    node->right = avl_tree_insert_n(node->right, key, value);
  
  balance = avl_tree_balance_n(node)
  if (balance > 1 && key < node->left->key)
    return avl_tree_rotl(tree, node);
  if (balance < -1 && key > node->right->key)
    return avl_tree_rotr(tree, node);
  if (balance > 1 && key > node->left->key) {
    node->left = avl_tree_rotl(tree, node->left);
    return avl_tree_rotr(tree, node);
  }
  if (balance < -1 && key < node->right->key) {
    node->right = avl_tree_rotl(tree, node->right);
    return avl_tree_rotl(tree, node);
  }
  
  return node;
}
  
avl_node *avl_tree_insert(avl_tree *tree, uint32_t key, void *value) {
  avl_node *node, *parent;
  
  node = avl_tree_search_n(tree, key);
  if (node) { // key already exists
    return 0; 
  }
  return avl_tree_insert_n(tree->root, key, value);
} 
