function [c3, c4, rates] = extract_channels(data, info)
    names = upper(string(data.Properties.VariableNames));
    idx3 = find(contains(names, 'C3'));
    idx4 = find(contains(names, 'C4'));
    assert(isscalar(idx3) && isscalar(idx4), 'Exactly one C3 and C4 channel required');
    c3 = unpack(data{:, idx3});
    c4 = unpack(data{:, idx4});
    if nargin > 1
        infoNames = upper(string(info.SignalLabels));
        rate3 = find(contains(infoNames, 'C3'));
        rate4 = find(contains(infoNames, 'C4'));
        assert(isscalar(rate3) && isscalar(rate4), 'Ambiguous EDF sample-rate metadata');
        rates = double(info.NumSamples([rate3 rate4])) / seconds(info.DataRecordDuration);
    else
        rates = [];
    end
end
function value = unpack(records)
    if iscell(records)
        records = cellfun(@(x) double(x(:)), records, 'UniformOutput', false);
        value = vertcat(records{:});
    else
        value = double(records(:));
    end
end
