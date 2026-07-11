function [c3, c4] = extract_channels(data)
    c3_col = find(contains(data.Properties.VariableNames, 'C3'));
    c4_col = find(contains(data.Properties.VariableNames, 'C4'));
    c3 = double(data{:, c3_col});
    c4 = double(data{:, c4_col});
end
