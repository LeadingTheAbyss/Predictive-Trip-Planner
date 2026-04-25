import { useState } from 'react'

function App() {
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchTripPlan = async (e) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      const response = await fetch('http://127.0.0.1:8000/plan-trip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ origin, destination })
      })
      
      const data = await response.json()
      setRecommendations(data.recommendations)
    } catch (error) {
      console.error("Failed to fetch data:", error)
      alert("Make sure your backend is running!")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-sans">
      <div className="max-w-2xl mx-auto space-y-8">
        
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">When-To-Go Planner</h1>
          <p className="text-gray-500">Predictive departure times based on traffic and crowds.</p>
        </div>

        <form onSubmit={fetchTripPlan} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Origin</label>
              <input 
                type="text" 
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="e.g. RGIPT"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Destination</label>
              <input 
                type="text" 
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="e.g. Mall"
                required
              />
            </div>
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
          >
            {loading ? 'Calculating...' : 'Find Best Departure Times'}
          </button>
        </form>

        <div className="space-y-4">
          {recommendations.map((rec, index) => (
            <div key={index} className={`p-4 rounded-xl border-l-4 shadow-sm bg-white flex justify-between items-center ${
              rec.status === 'BEST' ? 'border-green-500' : 
              rec.status === 'OK' ? 'border-yellow-500' : 'border-red-500'
            }`}>
              
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="text-xl font-bold text-gray-900">{rec.time_slot}</h3>
                  <span className={`text-xs font-bold px-2 py-1 rounded-full ${
                    rec.status === 'BEST' ? 'bg-green-100 text-green-700' : 
                    rec.status === 'OK' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {rec.status}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{rec.insight}</p>
              </div>

              <div className="text-right">
                <div className="text-lg font-bold text-gray-900">{rec.estimated_travel_time_mins} mins</div>
                <div className="text-sm text-gray-500">Crowd Level: {rec.crowd_level}/10</div>
              </div>

            </div>
          ))}
        </div>

      </div>
    </div>
  )
}

export default App