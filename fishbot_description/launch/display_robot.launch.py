import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    #获取默认路径
    urdf_tutorial_path = get_package_share_directory('fishbot_description')
    default_model_path = urdf_tutorial_path + '/urdf/fishbot/fishbot.urdf.xacro'#我把这里的路径改为了fishbot.urdf.xacro; 原来为/urdf/first_robot.urdf
    #default_model_path = urdf_tutorial_path + '/urdf/first_robot.urdf'#初始路径：/urdf/first_robot.urdf
    default_rviz_config_path = urdf_tutorial_path + '/config/rviz/display_model_complete.rviz'#默认rviz配置文件路径
    #为launch声明参数
    action_declare_arg_mode_path = launch.actions.DeclareLaunchArgument(
        name='model', default_value=str(default_model_path),
        description='URDF 的绝对路径')
    #获取文件内容生成新的参数
    robot_description = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.Command(
            ['xacro ', launch.substitutions.LaunchConfiguration('model')]),value_type=str)#在介绍了‘宏’用法后，将cat改为xacro
    #状态发布节点
    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}]
    )
    #关节发布节点
    joint_state_publisher_node = launch_ros.actions.Node(
        package='joint_state_publisher',executable='joint_state_publisher',
    )
    # Rviz节点
    rviz_node = launch_ros.actions.Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', default_rviz_config_path]#这里的arguments是复数（有多个数，不是带虚数的复数）形式，即带s
    )

    return launch.LaunchDescription([
        action_declare_arg_mode_path,
        joint_state_publisher_node,
        robot_state_publisher_node,
        rviz_node
    ])