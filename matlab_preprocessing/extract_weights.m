load('fcn_model.mat', 'fcnNet');
if ~exist('hardware/mif', 'dir')
    mkdir('hardware/mif');
end
layers = {'fc1', 'fc2', 'fc3', 'fc4'};
for L = 1:4
    layerName = layers{L};
    idx = find(arrayfun(@(l) strcmp(l.Name, layerName), fcnNet.Layers));
    layer = fcnNet.Layers(idx);
    W = layer.Weights;
    B = layer.Bias;
    numNeurons = size(W, 1);
    for n = 0:numNeurons-1
        w_n = W(n+1, :);
        w_fp = fi(w_n, 1, 16, 13);
        w_fid = fopen(sprintf('hardware/mif/w_%d_%d.mif', L, n), 'w');
        for i = 1:length(w_fp)
            fprintf(w_fid, '%s\n', bin(w_fp(i)));
        end
        fclose(w_fid);
        b_n = B(n+1);
        b_fp = fi(b_n, 1, 16, 13);
        b_fid = fopen(sprintf('hardware/mif/b_%d_%d.mif', L, n), 'w');
        fprintf(b_fid, '%s\n', bin(b_fp));
        fclose(b_fid);
    end
end
sig_fid = fopen('hardware/mif/sig_rom.mem', 'w');
for i = 0:1023
    x = (i - 512) / 128;
    s = 1 / (1 + exp(-x));
    s_fp = fi(s, 1, 16, 13);
    fprintf(sig_fid, '%s\n', bin(s_fp));
end
fclose(sig_fid);
load('dataset/eeg_test.mat', 'eeg_test');
load('dataset/test_labels.mat', 'test_labels');
numSimSamples = min(30, size(eeg_test, 1));
data_fid = fopen('hardware/mif/test_data.txt', 'w');
labels_fid = fopen('hardware/mif/test_labels.txt', 'w');
for i = 1:numSimSamples
    x_val = eeg_test(i, :);
    x_fcn = interp1(1:2816, x_val, linspace(1, 2816, 784));
    x_fp = fi(x_fcn, 1, 16, 13);
    for j = 1:784
        fprintf(data_fid, '%s\n', bin(x_fp(j)));
    end
    lbl = test_labels(i);
    lbl_bin = dec2bin(lbl, 4);
    fprintf(labels_fid, '%s\n', lbl_bin);
end
fclose(data_fid);
fclose(labels_fid);
