import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const TradingChart = () => {
  const [chartData, setChartData] = useState([]);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [selectedPair, setSelectedPair] = useState('BTC/USDT');

  // Generate sample chart data
  useEffect(() => {
    const generateData = () => {
      const data = [];
      let price = 44720;
      
      for (let i = 0; i < 50; i++) {
        price += (Math.random() - 0.5) * 1000;
        data.push({
          time: new Date(Date.now() - (49 - i) * 60000).toLocaleTimeString(),
          price: price,
          volume: Math.random() * 1000000
        });
      }
      
      setChartData(data);
    };

    generateData();
    const interval = setInterval(generateData, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, [selectedPair, selectedTimeframe]);

  const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];
  const tradingPairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT'];

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-bold text-white">Trading Chart</h2>
          <select 
            value={selectedPair} 
            onChange={(e) => setSelectedPair(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1 text-white text-sm focus:border-blue-500 focus:outline-none"
          >
            {tradingPairs.map(pair => (
              <option key={pair} value={pair}>{pair}</option>
            ))}
          </select>
        </div>
        
        <div className="flex space-x-2">
          {timeframes.map(tf => (
            <button
              key={tf}
              onClick={() => setSelectedTimeframe(tf)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                selectedTimeframe === tf
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="time" 
              stroke="#9CA3AF"
              fontSize={12}
            />
            <YAxis 
              stroke="#9CA3AF"
              fontSize={12}
              domain={['dataMin - 500', 'dataMax + 500']}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#F9FAFB'
              }}
            />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="#3B82F6" 
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex justify-between items-center text-sm">
        <div className="flex space-x-4">
          <div className="text-gray-400">
            Current: <span className="text-white font-semibold">${chartData[chartData.length - 1]?.price?.toFixed(2)}</span>
          </div>
          <div className="text-gray-400">
            24h Change: <span className="text-green-400 font-semibold">+3.4%</span>
          </div>
        </div>
        <div className="text-gray-400">
          Volume: <span className="text-white">28.5B</span>
        </div>
      </div>
    </div>
  );
};

export default TradingChart; 