#include <stdio.h>
#include <stdint.h>

#include "misc/suffix_tree.h"

#define suffix_tree_node_rep(rep,node) \
  sprintf(rep, "%c,%i ", node->value, node->idx);

int suffix_tree_node_width(trie_node *node) {
  char rep[10];
  suffix_tree_node_rep(rep, node);
  return strlen(rep);
}

int suffix_tree_width(trie_node *root) {
  trie_node *node;
  int width;
  char rep[10];
  
  if (!root)
    return 0;
  if (!root->child)
    return suffix_tree_node_width(root);
  
  width = 0;
  for (node=root->child;node;node=node->next) {
    width += suffix_tree_width(node);
  }
  return width;
}

void suffix_tree_print(suffix_tree *tree) {
  int i;
  trie_node *node;
  trie_node *row[2][1024];
  int node_count[2];
  int true_count;
  int width, pad, lpad, rpad;
  int buf;
  char rep[10];
  
  buf = 0;
  row[0][0] = tree->root;
  node_count[0] = 1;
  true_count = 1;
  while (true_count) {
	for (i=0;i<node_count[buf];i++) {
	  node = row[buf][i];
	  if ((uint32_t)node & 1) {
	    width = (uint32_t)node >> 1;
	    printf("%*s", width, "");
	    continue;
	  }
	  width = suffix_tree_width(node);
	  
	  pad = width - suffix_tree_node_width(node);
	  lpad = pad/2;
	  rpad = lpad + pad%2;
	  suffix_tree_node_rep(rep, node);
	  printf("%*s%s%*s", lpad, "", rep, rpad, "");
	} 
	printf("\n");
	node_count[1-buf] = 0; 
	true_count = 0;
	for (i=0;i<node_count[buf];i++) {
	  node = row[buf][i];
	  if ((uint32_t)node & 1) {
	    row[1-buf][node_count[1-buf]++] = node;
	    continue;
	  }
	  if (!node->child) {
		width = suffix_tree_node_width(node);
	    row[1-buf][node_count[1-buf]++] = (width << 1) | 1;
	    true_count++;
	  }
	  for (node=node->child;node;node=node->next) {
	    row[1-buf][node_count[1-buf]++] = node;
	    true_count++;
	  }
	}
    buf = 1-buf;
  }
}

void test(char *str) {
  
  int len;
  int i;
  suffix_tree *tree = malloc(sizeof(suffix_tree));
  
  len = strlen(str);
  suffix_tree_init(tree);
  for (i=0;i<len;i++) {
    suffix_tree_insert(tree, str[i], i); 
  }
  suffix_tree_print(tree);
  
  free(tree);
}
		
int main(int argc, char **argv) {
	
  char *str;
  
  str = argv[1];
  test(str);
	
  return 0;
}	
