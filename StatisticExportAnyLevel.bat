set /P InputValue="Set prefix level to: "
%~dp0/WwiseStatistic.exe --PrefixLevel %InputValue% --Integrated --Momentary --ShortTerm --LRA --TruePeak --Statistic