load('dataset/eeg_train_balanced.mat', 'eeg_train');
load('dataset/train_labels.mat', 'train_labels');
load('dataset/eeg_valid.mat', 'eeg_valid');
load('dataset/valid_labels.mat', 'valid_labels');
X_train_reshaped = reshape(eeg_train', [2816, 1, 1, size(eeg_train, 1)]);
X_valid_reshaped = reshape(eeg_valid', [2816, 1, 1, size(eeg_valid, 1)]);
Y_train = categorical(train_labels);
Y_valid = categorical(valid_labels);
layers = [
    imageInputLayer([2816 1 1], 'Normalization', 'none')
    batchNormalizationLayer
    convolution2dLayer([100 1], 3, 'Stride', [2 1], 'Padding', 'same')
    reluLayer
    maxPooling2dLayer([2 1], 'Stride', [2 1], 'Padding', 'same')
    convolution2dLayer([10 1], 50, 'Stride', [1 1], 'Padding', 'same')
    maxPooling2dLayer([2 1], 'Stride', [2 1], 'Padding', 'same')
    reluLayer
    convolution2dLayer([30 1], 30, 'Stride', [1 1], 'Padding', 'same')
    maxPooling2dLayer([2 1], 'Stride', [2 1], 'Padding', 'same')
    reluLayer
    batchNormalizationLayer
    fullyConnectedLayer(2)
    softmaxLayer
    classificationLayer
];
options = trainingOptions('adam', ...
    'MaxEpochs', 10, ...
    'MiniBatchSize', 64, ...
    'InitialLearnRate', 0.001, ...
    'ValidationData', {X_valid_reshaped, Y_valid}, ...
    'ValidationFrequency', 50, ...
    'Plots', 'none');
trainedNet = trainNetwork(X_train_reshaped, Y_train, layers, options);
save('global_model.mat', 'trainedNet');
X_train_fcn = zeros(size(eeg_train, 1), 784);
for i = 1:size(eeg_train, 1)
    X_train_fcn(i, :) = interp1(1:2816, eeg_train(i, :), linspace(1, 2816, 784));
end
X_valid_fcn = zeros(size(eeg_valid, 1), 784);
for i = 1:size(eeg_valid, 1)
    X_valid_fcn(i, :) = interp1(1:2816, eeg_valid(i, :), linspace(1, 2816, 784));
end
Y_train_fcn = categorical(train_labels, 0:9);
Y_valid_fcn = categorical(valid_labels, 0:9);
fcn_layers = [
    featureInputLayer(784, 'Normalization', 'none')
    fullyConnectedLayer(30, 'Name', 'fc1')
    reluLayer('Name', 'relu1')
    fullyConnectedLayer(30, 'Name', 'fc2')
    reluLayer('Name', 'relu2')
    fullyConnectedLayer(10, 'Name', 'fc3')
    sigmoidLayer('Name', 'sigmoid1')
    fullyConnectedLayer(10, 'Name', 'fc4')
    sigmoidLayer('Name', 'sigmoid2')
    softmaxLayer('Name', 'softmax')
    classificationLayer('Name', 'classoutput')
];
fcn_options = trainingOptions('adam', ...
    'MaxEpochs', 10, ...
    'MiniBatchSize', 64, ...
    'InitialLearnRate', 0.001, ...
    'ValidationData', {X_valid_fcn, Y_valid_fcn}, ...
    'ValidationFrequency', 50, ...
    'Plots', 'none');
fcnNet = trainNetwork(X_train_fcn, Y_train_fcn, fcn_layers, fcn_options);
save('fcn_model.mat', 'fcnNet');
