import numpy as np
import tensorflow as tf
import time
import data,warp,util

# build classification network
def fullCNN(opt,image):
	def conv2Layer(opt,feat,outDim):
		weight,bias = createVariable(opt,[3,3,int(feat.shape[-1]),outDim],stddev=opt.stdC)
		conv = tf.nn.conv2d(feat,weight,strides=[1,1,1,1],padding="VALID")+bias
		return conv
	def linearLayer(opt,feat,outDim):
		weight,bias = createVariable(opt,[int(feat.shape[-1]),outDim],stddev=opt.stdC)
		fc = tf.matmul(feat,weight)+bias
		return fc
	with tf.variable_scope("classifier"):
		feat = image
		with tf.variable_scope("conv1"):
			feat = conv2Layer(opt,feat,3)
			feat = tf.nn.relu(feat)
		with tf.variable_scope("conv2"):
			feat = conv2Layer(opt,feat,6)
			feat = tf.nn.relu(feat)
			feat = tf.nn.max_pool(feat,ksize=[1,2,2,1],strides=[1,2,2,1],padding="VALID")
		with tf.variable_scope("conv3"):
			feat = conv2Layer(opt,feat,9)
			feat = tf.nn.relu(feat)
		with tf.variable_scope("conv4"):
			feat = conv2Layer(opt,feat,12)
			feat = tf.nn.relu(feat)
		feat = tf.reshape(feat,[opt.batchSize,-1])
		with tf.variable_scope("fc5"):
			feat = linearLayer(opt,feat,48)
			feat = tf.nn.relu(feat)
		with tf.variable_scope("fc6"):
			feat = linearLayer(opt,feat,opt.labelN)
		output = feat
	return output

# build classification network
def CNN(opt,image):
	def conv2Layer(opt,feat,outDim):
		weight,bias = createVariable(opt,[9,9,int(feat.shape[-1]),outDim],stddev=opt.stdC)
		conv = tf.nn.conv2d(feat,weight,strides=[1,1,1,1],padding="VALID")+bias
		return conv
	def linearLayer(opt,feat,outDim):
		weight,bias = createVariable(opt,[int(feat.shape[-1]),outDim],stddev=opt.stdC)
		fc = tf.matmul(feat,weight)+bias
		return fc
	with tf.variable_scope("classifier"):
		feat = image
		with tf.variable_scope("conv1"):
			feat = conv2Layer(opt,feat,3)
			feat = tf.nn.relu(feat)
		feat = tf.reshape(feat,[opt.batchSize,-1])
		with tf.variable_scope("fc2"):
			feat = linearLayer(opt,feat,opt.labelN)
		output = feat
	return output

# build Spatial Transformer Network
def STN(opt,image):
	def conv2Layer(opt,feat,outDim):
		weight,bias = createVariable(opt,[7,7,int(feat.shape[-1]),outDim],stddev=opt.stdGP)
		conv = tf.nn.conv2d(feat,weight,strides=[1,1,1,1],padding="VALID")+bias
		return conv
	def linearLayer(opt,feat,outDim,final=False):
		weight,bias = createVariable(opt,[int(feat.shape[-1]),outDim],stddev=0.0 if final else opt.stdGP)
		fc = tf.matmul(feat,weight)+bias
		return fc
	imageWarpAll = [image]
	with tf.variable_scope("geometric"):
		feat = image
		with tf.variable_scope("conv1"):
			feat = conv2Layer(opt,feat,4)
			feat = tf.nn.relu(feat)
		with tf.variable_scope("conv2"):
			feat = conv2Layer(opt,feat,8)
			feat = tf.nn.relu(feat)
			feat = tf.nn.max_pool(feat,ksize=[1,2,2,1],strides=[1,2,2,1],padding="VALID")
		feat = tf.reshape(feat,[opt.batchSize,-1])
		with tf.variable_scope("fc3"):
			feat = linearLayer(opt,feat,48)
			feat = tf.nn.relu(feat)
		with tf.variable_scope("fc4"):
			feat = linearLayer(opt,feat,opt.warpDim,final=True)
		p = feat
	pMtrx = warp.vec2mtrx(opt,p)
	imageWarp = warp.transformImage(opt,image,pMtrx)
	imageWarpAll.append(imageWarp)
	return imageWarpAll

# build Inverse Compositional STN
def ICSTN(opt,image,p):
	def conv2Layer(opt,feat,outDim):
		weight,bias = createVariable(opt,[7,7,int(feat.shape[-1]),outDim],stddev=opt.stdGP)
		conv = tf.nn.conv2d(feat,weight,strides=[1,1,1,1],padding="VALID")+bias
		return conv
	def linearLayer(opt,feat,outDim,final=False):
		weight,bias = createVariable(opt,[int(feat.shape[-1]),outDim],stddev=0.0 if final else opt.stdGP)
		fc = tf.matmul(feat,weight)+bias
		return fc
	imageWarpAll = []
	for l in range(opt.warpN):
		with tf.variable_scope("geometric",reuse=l>0):
			pMtrx = warp.vec2mtrx(opt,p)
			imageWarp = warp.transformImage(opt,image,pMtrx)
			imageWarpAll.append(imageWarp)
			feat = imageWarp
			with tf.variable_scope("conv1"):
				feat = conv2Layer(opt,feat,4)
				feat = tf.nn.relu(feat)
			with tf.variable_scope("conv2"):
				feat = conv2Layer(opt,feat,8)
				feat = tf.nn.relu(feat)
				feat = tf.nn.max_pool(feat,ksize=[1,2,2,1],strides=[1,2,2,1],padding="VALID")
			feat = tf.reshape(feat,[opt.batchSize,-1])
			with tf.variable_scope("fc3"):
				feat = linearLayer(opt,feat,48)
				feat = tf.nn.relu(feat)
			with tf.variable_scope("fc4"):
				feat = linearLayer(opt,feat,opt.warpDim,final=True)
			dp = feat
		p = warp.compose(opt,p,dp)
	pMtrx = warp.vec2mtrx(opt,p)
	imageWarp = warp.transformImage(opt,image,pMtrx)
	imageWarpAll.append(imageWarp)
	return imageWarpAll

# auxiliary function for creating weight and bias
def createVariable(opt,weightShape,biasShape=None,stddev=None):
	if biasShape is None: biasShape = [weightShape[-1]]
	weight = tf.get_variable("weight",shape=weightShape,dtype=tf.float32,
									  initializer=tf.random_normal_initializer(stddev=stddev))
	bias = tf.get_variable("bias",shape=biasShape,dtype=tf.float32,
								  initializer=tf.random_normal_initializer(stddev=stddev))
	return weight,bias
