import launch
import launch_ros
from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # 获取默认路径
    robot_name_in_model = "fishbot"
    urdf_tutorial_path = get_package_share_directory('fishbot_description')
    default_model_path = urdf_tutorial_path + "/urdf/fishbot/fishbot.urdf.xacro"
    default_world_path = urdf_tutorial_path + "/world/custom_room.sdf"
    # 获取bridge参数,这个我自己添加的
    bridge_params_path_path = urdf_tutorial_path + "/params/fishbot_bridge.yaml"
    # 为launch声明参数
    action_declare_arg_mode_path = launch.actions.DeclareLaunchArgument(
        name='model',default_value=str(default_model_path),
        description='URDF 的绝对路径')
    #获取文件内容生成新的参数
    robot_description = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.Command(
            ['xacro ', launch.substitutions.LaunchConfiguration('model')]),value_type=str
        )
    #将由xacro转化成的urdf文件传递给robot_state_publisher,并发布
    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description':robot_description}]
    )

    #通过 IncludeLaunchDescription 包含另外一个 launch文件
    launch_gazebo = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource([get_package_share_directory('ros_gz_sim'),'/launch/gz_sim.launch.py']),
            #传递参数
        launch_arguments={
            'gz_args': default_world_path,
            'verbose': 'true',
        }.items(),
    )

    # 请求Gazebo 加载机器人                      
    spawn_entity_node=launch_ros.actions.Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            'name',robot_name_in_model,
            '-topic','/robot_description',
        ],
        output='screen',
    )
    
    # 发布bridge节点（这个是参考harmonic tutorial新手引导我自己添加的内容），包括关节状态节点
    start_gazebo_ros_bridge_cmd = launch_ros.actions.Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params_path_path}',
        ],
        output='screen',
    )
    # 这个是图像信息通信的bridge
    start_gazebo_ros_image_bridge_cmd = launch_ros.actions.Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=['/camera/image_raw'],
        output='screen',
    )

    #加载并激活 fishbot_joint_state_broadcaster
    load_joint_state_controller = launch.actions.ExecuteProcess(
        cmd=['ros2','control','load_controller','--set-state','active',
             'fishbot_joint_state_broadcaster'],
        output='screen')
    #加载并激活 fishbot_effort_controller 控制器(力控)
    load_fishbot_effort_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'fishbot_effort_controller'], 
        output='screen')
    #加载并激活 fishbot_diff_drive_controller 控制器(两轮差速计)
    load_fishbot_diff_drive_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'fishbot_diff_drive_controller'], 
        output='screen')
    
    return launch.LaunchDescription([
        action_declare_arg_mode_path,
        robot_state_publisher_node,
        launch_gazebo,
        spawn_entity_node,
        #事件动作，当加载机器人结束后执行
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=spawn_entity_node,
                on_exit=[load_joint_state_controller],)
        ),
        #事件动作，当load_joint_state_controller结束后执行
        # 暂时启动力控就注释掉差速，反之亦然；
        # 之后可以都不在此启动，只是在.yaml和.urdf中配置下,需要哪个就在命令行启动哪个
        # launch.actions.RegisterEventHandler(
        #     event_handler=launch.event_handlers.OnProcessExit(
        #         target_action=load_joint_state_controller,
        #         on_exit=[load_fishbot_effort_controller],
        #     )
        # ),
        #事件动作，当……结束后执行，差速器用
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=load_joint_state_controller, 
                on_exit=[load_fishbot_diff_drive_controller],
            )
        ),
        start_gazebo_ros_bridge_cmd,
        start_gazebo_ros_image_bridge_cmd,
    ])

