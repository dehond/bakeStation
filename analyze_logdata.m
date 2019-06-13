%analyze_logdata.m
close all;
files = dir('logdata/*.csv');
nfiles = length(files);

for i = (nfiles-10):nfiles
    try
        fdum = files(i).name;
        file = fdum(1:end-4);
        rawdat = csvread(['logdata/' file '.csv'], 1, 1);
        si = size(rawdat);
        times = datetime(rawdat(:,1), 'convertfrom', 'posixtime', 'timezone', 'local');
        
        figure;
        ax = axes; box on;
        if si(2) == 2
            plot(times, rawdat(:,2));
        elseif si(2) == 3
            ax = gca;
            
            yyaxis(ax, 'left');
            semilogy(times, rawdat(:,2), 'color', 'black');
            ax.YAxis(1).Color = 'black';
            ax.YAxis(1).Label.String = 'Pressure (torr)';
            
            yyaxis(ax, 'right');
            plot(times, rawdat(:,3), 'color', 'red');
            ax.YAxis(2).Color = 'red';
            ax.YAxis(2).Label.String = 'Temperature (°C)';
        end
        
        savefig(gcf, ['logfigs/' file '.fig']);
        print(gcf, ['logfigs/' file '.png'], '-dpng');
        close all;
    end
end