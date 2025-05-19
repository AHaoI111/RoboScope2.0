import { useState,useEffect  } from 'react';
import './App.css';
import config from './IPconfig';


function Menu({ onPageChange }) {
    return (
        <div className="menu">
            <button onClick={() => onPageChange('home')}>主页</button>
            <button onClick={() => onPageChange('deviceInfo')}>设备信息</button>
            <button onClick={() => onPageChange('devicecenter')}>设备中心</button>
            <button onClick={() => onPageChange('scan')}>扫描中心</button>
            <button onClick={() => onPageChange('settings')}>设置</button>
        </div>
    );
}

function HomePage() {
    return (
        <div>
            <h1>RoBoScope2.0</h1>
            <h2>显微扫描测试平台</h2>
            {/* 显示图片 */}
            <img src="./kms.png" alt="RoBoScope" width={400} />
            {/*<p>2025.04.24</p>*/}
        </div>
    );
}

function DeviceInfoPage() {
    // 用于存储设备信息
    const [deviceInfo, setDeviceInfo] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const serverIp = config.serverIp;

    // 发送请求获取设备信息的函数
    const fetchDeviceInfo = async () => {
        setLoading(true); // 设置为加载状态
        setError(null);   // 清空错误信息
        try {
            // 这里的 URL 是示例，你应该根据实际的 API 替换它
            const response = await fetch(serverIp+'/roboscope_info');

            // 如果请求成功并且返回状态为200
            if (!response.ok) {
                throw new Error('获取设备信息失败');
            }

            const data = await response.json(); // 解析返回的 JSON 数据
            setDeviceInfo(data); // 将设备信息保存到状态
        } catch (err) {
            setError(err.message); // 如果请求失败，设置错误信息
        } finally {
            setLoading(false); // 无论成功或失败，都结束加载状态
        }
    };

    return (
        <div>
            <h1>设备信息获取</h1>
            {/* 按钮，点击时发送请求 */}
            <button onClick={fetchDeviceInfo} disabled={loading}>
                {loading ? '加载中...' : '获取设备信息'}
            </button>
            {/* 如果有错误，显示错误信息 */}
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {/* 如果设备信息存在，显示设备信息 */}
            {deviceInfo && (
                <div>
                    <h2>设备信息:</h2>
                    <p>{JSON.stringify(deviceInfo, null, 2)}</p> {/* 格式化设备信息 */}
                </div>
            )}
        </div>
    );
}

function DeviceCenterPage() {
    const [isConnected, setIsConnected] = useState(false);
    const serverIp = config.serverIp;
    // 在页面加载时获取连接状态
    useEffect(() => {
        // 使用 async/await 来处理异步操作
        const fetchConnectionStatus = async () => {
            try {
                const response = await fetch(serverIp + '/getConnectionStatus', {
                    method: 'GET',  // 这里使用 GET 请求获取状态
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    throw new Error('请求失败');
                }

                const data = await response.json();
                alert("当前连接状态：" +data);
                setIsConnected(data);  // 假设返回的 data 中包含 isConnected 字段
            } catch (error) {
                alert("获取连接状态失败：" + error);
            }
        };

        // 立即调用异步函数
        fetchConnectionStatus();

    }, [serverIp]); // 依赖 serverIp，如果 serverIp 变化时重新请求
    const connect = async () => {
        try {
            const response = await fetch(serverIp+'/connect2device', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({   })
            });
            if (!response.ok) {
                throw new Error('请求失败');
            }

            const data = await response.json();
            alert(` 连接成功，服务器响应：${data.message}`);
            setIsConnected(true);
        } catch (error) {
            alert("请求失败"+error);
        }
    };

    const disconnect = async () => {
        try {
            const response = await fetch(serverIp+'/disconnect2device', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({  })
            });

            if (!response.ok) {
                throw new Error('请求失败');
            }
            const data = await response.json();
            alert(` 取消连接成功，服务器响应：${data.message}`);
            setIsConnected(false);
        } catch (error) {
            alert("请求失败"+error);
        }
    };
    return (
        <div>
            <h1>设备中心</h1>
            <p>用于连接设备和关闭连接</p>
            {/* 连接设备 */}
            <div>
                <button
                    onClick={connect} disabled={isConnected}>连接设备

                </button>
            </div>

            {/* 取消连接设备 */}
            <div>
                <button
                    onClick={disconnect} disabled={!isConnected}>断开连接

                </button>
            </div>
        </div>
    );
}

function ScanPage() {
    const [selectedOption, setSelectedOption] = useState(''); // 默认没有选项
    const [scanOptions, setScanOptions] = useState([]); // 用来存储从服务器获取的扫描方案
    const serverIp = config.serverIp;
    const [matrix, setMatrix] = useState([
        Array(24).fill(1), // 第一盒子的24个位置初始化为1
        Array(24).fill(1), // 第二盒子
        Array(24).fill(1), // 第三盒子
        Array(24).fill(1)  // 第四盒子
    ]);

    // 使用 useEffect 在组件加载时发起请求获取扫描方案
    useEffect(() => {
        // 模拟一个获取扫描方案的网络请求
        const fetchScanOptions = async () => {
            try {
                // 假设 API 返回的是扫描方案数组
                const response = await fetch(serverIp+'/getplan'); // 替换为你的服务器 API
                const data = await response.json();


                setScanOptions(data); // 更新扫描方案
                if (data.length > 0) {
                    setSelectedOption(data[1].value); // 设置默认选项为第一个方案
                }
            } catch (error) {
                console.error('获取扫描方案失败', error);
            }
        };

        fetchScanOptions(); // 发起请求
    }, []); // 空依赖数组表示只在组件挂载时执行一次
    // 处理下拉框变化
    const handleSelectChange = (event) => {
        setSelectedOption(event.target.value);
    };
    // 处理勾选框变化
    const handleCheckboxChange = (boxIndex, positionIndex) => {
        const newMatrix = [...matrix];
        newMatrix[boxIndex][positionIndex] = newMatrix[boxIndex][positionIndex] === 1 ? 0 : 1;
        setMatrix(newMatrix);
    };
    const scan_start = async () => {
        alert(`服务器响应：`+matrix);
        try {
            const response = await fetch(serverIp + '/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({plan: selectedOption, slide_list: matrix})
            });

            if (!response.ok) {
                throw new Error('请求失败');
            }

            const data = await response.json();
            alert(`服务器响应：${data.message}`);
        } catch (error) {
            alert("请求失败"+error);
        }
    };
    return (
        <div>
            <h1>扫描中心</h1>
            <p>用于测试扫描方案</p>

            {/* 如果 scanOptions 为空，显示加载状态 */}
            {scanOptions.length === 0 ? (
                <p>加载扫描方案...</p>
            ) : (
                <div>
                    {/* 下拉选择框 */}
                    <div>
                        <label htmlFor="scanOption">选择扫描方案:</label>
                        <select
                            id="scanOption"
                            value={selectedOption}
                            onChange={handleSelectChange}
                        >
                            {scanOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                    {option.value}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <h2>选择玻片盒子</h2>
                        <div style={{display: 'flex', gap: '10px'}}>
                            {matrix.map((box, boxIndex) => (
                                <div key={boxIndex} style={{
                                    border: '1px solid #ccc',
                                    padding: '8px',
                                    width: '100px',
                                    display: 'flex',
                                    flexDirection: 'column-reverse'
                                }}>
                                    <h3 style={{fontSize: '14px', marginBottom: '5px'}}>盒子 {boxIndex + 1}</h3>
                                    {box.map((position, positionIndex) => (
                                        <div key={positionIndex} style={{marginBottom: '5px'}}>
                                            <label style={{fontSize: '14px', display: 'flex', alignItems: 'center'}}>
                                                <input
                                                    type="checkbox"
                                                    checked={position === 0}
                                                    onChange={() => handleCheckboxChange(boxIndex, positionIndex)}
                                                    style={{marginRight: '5px'}}
                                                />
                                                {positionIndex + 1}
                                            </label>
                                        </div>
                                    ))}
                                </div>
                            ))}
                        </div>
                    </div>
                    <div>
                        <button onClick={scan_start}>扫描测试</button>
                    </div>
                </div>
            )}
        </div>
    );
}

function SettingsPage() {
    // 用于存储 X、Y、Z 轴的数值

    const [microscope_xValue, setXValue_microscope] = useState(0);
    const [microscope_yValue, setYValue_microscope] = useState(0);
    const [microscope_zValue, setZValue_microscope] = useState(0);
    const [loader_xValue, setXValue_loader] = useState(0);
    const [loader_yValue, setYValue_loader] = useState(0);
    const [loader_zValue, setZValue_loader] = useState(0);
    const [imageBase64, setImageBase64] = useState(null);
    const [camera, setcamera] = useState('');

    // API 请求地址（假设的服务器地址）
    const serverIp = config.serverIp;

    // 发送请求并控制位移台 Z 轴
    const get_slide = async () => {
        try {
            const response = await fetch(serverIp + '/testgetslide', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });

            if (!response.ok) {
                throw new Error('请求失败');
            }

            const data = await response.json();
            alert(`服务器响应：${data.message}`);
        } catch (error) {
            alert("请求失败" + error);
        }
    };
    // 发送请求并控制位移台 Z 轴
    const put_slide = async () => {
        try {
            const response = await fetch(serverIp+'/testputslide', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({  })
            });

            if (!response.ok) {
                throw new Error('请求失败');
            }

            const data = await response.json();
            alert(`服务器响应：${data.message}`);
        } catch (error) {
            alert("请求失败"+error);
        }
    };


    // 发送请求并控制位移台 X 轴
    const microscope_moveX = async () => {
        try {
            const response = await fetch(serverIp+'/microscopemovex2', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({  value: microscope_xValue })
            });

            if (!response.ok) {
                throw new Error('请求失败');
            }

            const data = await response.json();
            alert(`X轴移动了 ${microscope_xValue} 单位，服务器响应：${data.message}`);
        } catch (error) {
            alert("请求失败，无法移动 X 轴！"+error);
        }
    };

    // 发送请求并控制位移台 Y 轴
    const microscope_moveY = async () => {
        try {
            const response = await fetch(serverIp+'/microscopemovey2', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({  value: microscope_yValue })
            });

            if (!response.ok) {
                throw new Error('请求失败');
            }

            const data = await response.json();
            alert(`Y轴移动了 ${microscope_yValue} 单位，服务器响应：${data.message}`);
        } catch (error) {
            alert("请求失败，无法移动 Y 轴！"+error);
        }
    };

    // 发送请求并控制位移台 Z 轴
    const microscope_moveZ = async () => {
        try {
            const response = await fetch(serverIp+'/microscopemovez2', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ value: microscope_zValue })
            });

            if (!response.ok) {
                throw new Error('请求失败');
            }

            const data = await response.json();
            alert(`Z轴移动了 ${microscope_zValue} 单位，服务器响应：${data.message}`);
        } catch (error) {
            alert("请求失败，无法移动 Z 轴！"+error);
        }
    };

    // 发送请求并控制位移台 X 轴
    const loader_moveX = async () => {
        try {
            const response = await fetch(serverIp+'/loadermovex2', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ value: loader_xValue })
            });

            if (!response.ok) {
                throw new Error('请求失败');
            }

            const data = await response.json();
            alert(`X轴移动了 ${loader_xValue} 单位，服务器响应：${data.message}`);
        } catch (error) {
            alert("请求失败，无法移动 X 轴！"+error);
        }
    };

    // 发送请求并控制位移台 Y 轴
    const loader_moveY = async () => {
        try {
            const response = await fetch(serverIp+'/loadermovey2', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({  value: loader_yValue })
            });

            if (!response.ok) {
                throw new Error('请求失败');
            }

            const data = await response.json();
            alert(`Y轴移动了 ${loader_yValue} 单位，服务器响应：${data.message}`);
        } catch (error) {
            alert("请求失败，无法移动 Y 轴！"+error);
        }
    };

    // 发送请求并控制位移台 Z 轴
    const loader_moveZ = async () => {
        try {
            const response = await fetch(serverIp+'/loadermovez2', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ value: loader_zValue })
            });

            if (!response.ok) {
                throw new Error('请求失败');
            }

            const data = await response.json();
            alert(`Z轴移动了 ${loader_zValue} 单位，服务器响应：${data.message}`);
        } catch (error) {
            alert("请求失败，无法移动 Z 轴！"+error);
        }
    };

    const test_autofcous = async () => {
        try {
            const response = await fetch(serverIp+'/autofcous', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ camera: camera })
            });

            if (!response.ok) {
                throw new Error('请求失败');
            }

            const data = await response.json();
            alert(`服务器响应：${data.result}`);
            if (data.data) {
                setImageBase64(data.data);
            } else {
                alert('没有收到有效的 Base64 数据');
            }
        } catch (error) {
            alert("请求失败"+error);
        }
    };

    return (
        <div>
            <h1>设备调试</h1>
            <div>
                <div>
                    <button onClick={get_slide}>取片</button>
                </div>
                <div>
                    <button onClick={put_slide}>送片</button>
                </div>

                <h2>位移台调试</h2>
                <div>
                    <label>显微镜X轴位移: </label>
                    <input
                        type="number"
                        value={microscope_xValue}
                        onChange={(e) => setXValue_microscope(Number(e.target.value))}
                        placeholder="输入 X 轴值"
                    />
                    <button onClick={microscope_moveX}>移动 X 轴</button>
                </div>
                <div>
                    <label>显微镜Y轴位移: </label>
                    <input
                        type="number"
                        value={microscope_yValue}
                        onChange={(e) => setYValue_microscope(Number(e.target.value))}
                        placeholder="输入 Y 轴值"
                    />
                    <button onClick={microscope_moveY}>移动 Y 轴</button>
                </div>
                <div>
                    <label>显微镜Z轴位移: </label>
                    <input
                        type="number"
                        value={microscope_zValue}
                        onChange={(e) => setZValue_microscope(Number(e.target.value))}
                        placeholder="输入 Z 轴值"
                    />
                    <button onClick={microscope_moveZ}>移动 Z 轴</button>
                </div>

                <h2>装载器调试</h2>
                <div>
                    <label>装载器X轴位移: </label>
                    <input
                        type="number"
                        value={loader_xValue}
                        onChange={(e) => setXValue_loader(Number(e.target.value))}
                        placeholder="输入 X 轴值"
                    />
                    <button onClick={loader_moveX}>移动 X 轴</button>
                </div>
                <div>
                    <label>装载器Y轴位移: </label>
                    <input
                        type="number"
                        value={loader_yValue}
                        onChange={(e) => setYValue_loader(Number(e.target.value))}
                        placeholder="输入 Y 轴值"
                    />
                    <button onClick={loader_moveY}>移动 Y 轴</button>
                </div>
                <div>
                    <label>装载器Z轴位移: </label>
                    <input
                        type="number"
                        value={loader_zValue}
                        onChange={(e) => setZValue_loader(Number(e.target.value))}
                        placeholder="输入 Z 轴值"
                    />
                    <button onClick={loader_moveZ}>移动 Z 轴</button>
                </div>

                <h2>自动对焦测试</h2>
                <div>
                    <label>自动对焦测试: </label>
                    <input
                        type="text"
                        value={camera}
                        onChange={(e) => setcamera(e.target.value)}
                        placeholder="输入相机(high/low/single)"
                    />
                    <button onClick={test_autofcous}>自动对焦测试</button>
                    {/* 如果 Base64 数据存在，渲染图像 */}
                    {imageBase64 && (
                        <img
                            src={`data:image/jpeg;base64,${imageBase64}`}
                            alt="Loaded Image"
                            style={{width: '1200px', height: 'auto'}}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}

export default function App() {
    const [currentPage, setCurrentPage] = useState('home'); // 默认显示主页

    const handlePageChange = (page) => {
        setCurrentPage(page); // 切换页面
    };

    let pageContent;
    switch (currentPage) {
        case 'home':
            pageContent = <HomePage/>;
            break;
        case 'deviceInfo':
            pageContent = <DeviceInfoPage/>;
            break;
        case 'devicecenter':
            pageContent = <DeviceCenterPage />;
            break;
        case 'settings':
            pageContent = <SettingsPage />;
            break;
        case 'scan':
            pageContent = <ScanPage />;
            break;
        default:
            pageContent = <HomePage />;
            break;
    }

    return (
        <div style={{ display: 'flex', height: '100vh' }}>
            <Menu onPageChange={handlePageChange} />
            <div className="content">
                {pageContent}
            </div>
        </div>
    );
}
