import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area, Legend
} from 'recharts';

const COLORS = ['#4f46e5', '#ec4899', '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'];

const DataChart = ({ data, config }) => {
  if (!config || config.type === 'none') return null;

  const { type, x_axis, y_axis, title, image_url } = config;
  const BACKEND_URL = 'http://localhost:5000';

  // If we have a server-side generated image, prioritize it
  if (image_url) {
    return (
      <div className="chart-wrapper premium-chart">
        {title && <div className="chart-title-label">{title}</div>}
        <div className="chart-image-container premium-shadow">
          <div className="professional-badge">Professional Analysis</div>
          <img 
            src={`${BACKEND_URL}${image_url}`} 
            alt={title || 'Data Visualization'} 
            className="generated-chart-img"
            style={{ 
              width: '100%', 
              borderRadius: '12px', 
              marginTop: '10px',
              border: '1px solid rgba(255,255,255,0.1)',
              boxShadow: '0 10px 30px rgba(0,0,0,0.5)'
            }}
          />
        </div>
        <div className="query-label" style={{ marginTop: '12px', fontSize: '10px', opacity: 0.6, textAlign: 'right', fontStyle: 'italic' }}>
          Visualized via Gemini Engine: Matplotlib & Seaborn
        </div>
      </div>
    );
  }

  // Fallback to Recharts if no image_url but data is present
  if (!data || data.length === 0) return null;
  if (!data[0].hasOwnProperty(x_axis) || !data[0].hasOwnProperty(y_axis)) {
    return null;
  }

  const renderChart = () => {
    switch (type.toLowerCase()) {
      case 'bar':
        return (
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey={x_axis} stroke="#94a3b8" fontSize={12} />
            <YAxis stroke="#94a3b8" fontSize={12} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1A1F2C', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
              itemStyle={{ color: '#f8fafc' }}
            />
            <Legend />
            <Bar dataKey={y_axis} fill="url(#colorGradient)" radius={[4, 4, 0, 0]} />
            <defs>
              <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#ec4899" stopOpacity={0.8}/>
              </linearGradient>
            </defs>
          </BarChart>
        );
      case 'line':
        return (
          <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey={x_axis} stroke="#94a3b8" fontSize={12} />
            <YAxis stroke="#94a3b8" fontSize={12} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1A1F2C', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
            />
            <Legend />
            <Line type="monotone" dataKey={y_axis} stroke="#ec4899" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
          </LineChart>
        );
      case 'area':
        return (
          <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey={x_axis} stroke="#94a3b8" fontSize={12} />
            <YAxis stroke="#94a3b8" fontSize={12} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1A1F2C', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
            />
            <Legend />
            <Area type="monotone" dataKey={y_axis} stroke="#4f46e5" fillOpacity={1} fill="url(#colorArea)" />
            <defs>
              <linearGradient id="colorArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
              </linearGradient>
            </defs>
          </AreaChart>
        );
      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey={y_axis}
              nameKey={x_axis}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ backgroundColor: '#1A1F2C', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
            />
            <Legend />
          </PieChart>
        );
      default:
        return null;
    }
  };

  return (
    <div className="chart-wrapper">
      {title && <div className="chart-title-label">{title}</div>}
      <div className="chart-container-inner" style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DataChart;
