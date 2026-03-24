-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 24, 2026 at 09:11 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `fixitnow`
--

-- --------------------------------------------------------

--
-- Table structure for table `app_users`
--

CREATE TABLE `app_users` (
  `id` int(11) NOT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(20) DEFAULT NULL,
  `otp` varchar(6) DEFAULT NULL,
  `otp_expiry` datetime DEFAULT NULL,
  `house_number` varchar(50) DEFAULT NULL,
  `area` varchar(100) DEFAULT NULL,
  `street` varchar(100) DEFAULT NULL,
  `city` varchar(50) DEFAULT NULL,
  `state` varchar(50) DEFAULT NULL,
  `pincode` varchar(10) DEFAULT NULL,
  `landmark` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `booking_date` varchar(50) DEFAULT NULL,
  `booking_time` varchar(50) DEFAULT NULL,
  `booking_description` varchar(1000) DEFAULT NULL,
  `booked_technician_id` int(11) DEFAULT NULL,
  `booked_technician_name` varchar(255) DEFAULT NULL,
  `booking_status` varchar(50) DEFAULT NULL,
  `latitude` varchar(50) DEFAULT NULL,
  `longitude` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `app_users`
--

INSERT INTO `app_users` (`id`, `full_name`, `email`, `phone`, `password`, `role`, `otp`, `otp_expiry`, `house_number`, `area`, `street`, `city`, `state`, `pincode`, `landmark`, `created_at`, `booking_date`, `booking_time`, `booking_description`, `booked_technician_id`, `booked_technician_name`, `booking_status`, `latitude`, `longitude`) VALUES
(1, 'dineshhhh', 'ch@gmail.com', '9879879879', '123', 'Customer', NULL, NULL, '22H8+654', 'Kuthambakkam', 'N/A', 'Kuthambakkam', 'Tamil Nadu', '602105', NULL, '2026-03-04 13:29:52', NULL, NULL, NULL, NULL, NULL, NULL, '13.0282436', '80.0156868'),
(33, 'sapota', 'sapota@gmail.com', '9876543219', 'Sapota@#123', 'Technician', NULL, NULL, 'Block-L', 'Chembarambakkam', 'N/A', 'Chembarambakkam', 'Tamil Nadu', '600123', NULL, '2026-03-23 19:19:43', NULL, NULL, NULL, NULL, NULL, NULL, '13.0290896', '80.0348218'),
(34, 'System Admin', 'admin@fixitnow.com', '0000000000', 'admin123', 'admin', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-03-23 19:27:22', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(35, 'swagath', 'mr.swagath72@gmail.com', '7286845689', 'Swagath@#123', 'Technician', NULL, NULL, '1600', 'Mountain View', 'Amphitheatre Parkway', 'Mountain View', 'California', '94043', '1600', '2026-03-23 21:05:31', NULL, NULL, NULL, NULL, NULL, NULL, '13.0283146', '80.0158941'),
(36, 'absjfb', 'nibba@gmail.com', '7578594958', 'Nibba@#123', 'Technician', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-03-23 22:03:17', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(37, 'text', 'test@gmail.com', '2222222222', 'Test@#123', 'Customer', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-03-24 03:22:05', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `bookings`
--

CREATE TABLE `bookings` (
  `id` int(11) NOT NULL,
  `customer_email` varchar(255) NOT NULL,
  `technician_email` varchar(255) NOT NULL,
  `technician_name` varchar(255) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `date` varchar(50) DEFAULT NULL,
  `time` varchar(50) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `status` varchar(50) DEFAULT 'Pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `cost` varchar(50) DEFAULT NULL,
  `service_name` varchar(255) DEFAULT NULL,
  `technician_id` int(11) DEFAULT NULL,
  `customer_name` varchar(255) DEFAULT NULL,
  `work_photo_url` varchar(255) DEFAULT NULL,
  `rating_value` int(11) DEFAULT NULL,
  `rating_comment` varchar(255) DEFAULT NULL,
  `payment_status` varchar(50) DEFAULT 'Pending',
  `razorpay_order_id` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bookings`
--

INSERT INTO `bookings` (`id`, `customer_email`, `technician_email`, `technician_name`, `address`, `date`, `time`, `description`, `status`, `created_at`, `cost`, `service_name`, `technician_id`, `customer_name`, `work_photo_url`, `rating_value`, `rating_comment`, `payment_status`, `razorpay_order_id`) VALUES
(47, 'ch@gmail.com', 'sapota@gmail.com', 'sapota', 'Block-N, Kg Centre Point, Chembarambakkam, Tamil Nadu 600123, India', '24/03/2026', '01:12 AM', 'ghg', 'Completed', '2026-03-23 19:42:23', 'From ₹249', 'Light Installation', 33, 'dineshhhh', NULL, 5, 'excellent', 'Paid', NULL),
(48, 'ch@gmail.com', 'sapota@gmail.com', 'sapota', '22H8+654, Kuthambakkam, Tamil Nadu 602105, India', '24/03/2026', '10:00 AM', 'bbhgg', 'Pending', '2026-03-24 04:30:23', 'From ₹249', 'Light Installation', 33, 'dineshhhh', NULL, NULL, NULL, 'Pending', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `customer_profiles`
--

CREATE TABLE `customer_profiles` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `language` varchar(50) DEFAULT NULL,
  `profile_pic_url` varchar(255) DEFAULT NULL,
  `wallet_balance` varchar(50) DEFAULT '₹250.00'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `customer_profiles`
--

INSERT INTO `customer_profiles` (`id`, `user_id`, `language`, `profile_pic_url`, `wallet_balance`) VALUES
(1, 1, 'English (US)', '/uploads/profile_1_1773670692.jpg', '₹250.00'),
(10, 37, 'English (US)', NULL, '₹250.00');

-- --------------------------------------------------------

--
-- Table structure for table `messages`
--

CREATE TABLE `messages` (
  `id` int(11) NOT NULL,
  `sender_email` varchar(255) NOT NULL,
  `receiver_email` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `timestamp` datetime DEFAULT current_timestamp(),
  `is_read` tinyint(1) DEFAULT 0,
  `status` varchar(20) DEFAULT 'sent'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `messages`
--

INSERT INTO `messages` (`id`, `sender_email`, `receiver_email`, `message`, `timestamp`, `is_read`, `status`) VALUES
(36, 'sapota@gmail.com', 'ch@gmail.com', 'hi', '2026-03-24 01:26:32', 0, 'read');

-- --------------------------------------------------------

--
-- Table structure for table `technician_documents`
--

CREATE TABLE `technician_documents` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `doc_type` varchar(100) DEFAULT NULL,
  `file_url` varchar(255) DEFAULT NULL,
  `uploaded_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `technician_documents`
--

INSERT INTO `technician_documents` (`id`, `user_id`, `doc_type`, `file_url`, `uploaded_at`) VALUES
(10, 32, 'Identity Proof', '/uploads/tech_doc_32_identity_proof_1774293152.jpg', '2026-03-24 00:42:32'),
(11, 32, 'Skill Certificate', '/uploads/tech_doc_32_skill_certificate_1774293152.jpg', '2026-03-24 00:42:32'),
(12, 32, 'Work Photos', '/uploads/tech_doc_32_work_photos_1774293152.jpg', '2026-03-24 00:42:32'),
(13, 33, 'Identity Proof', '/uploads/tech_doc_33_identity_proof_1774293615.jpg', '2026-03-24 00:50:15'),
(14, 33, 'Work Photos', '/uploads/tech_doc_33_work_photos_1774293615.jpg', '2026-03-24 00:50:15'),
(15, 33, 'Skill Certificate', '/uploads/tech_doc_33_skill_certificate_1774293615.jpg', '2026-03-24 00:50:15'),
(16, 35, 'ID Card', '/uploads/mock_doc.pdf', '2026-03-24 03:02:14'),
(17, 35, 'Certificate', '/uploads/mock_doc.pdf', '2026-03-24 03:02:14'),
(18, 35, 'Experience Letter', '/uploads/mock_doc.pdf', '2026-03-24 03:02:14'),
(19, 36, 'ID Card', '/uploads/mock_doc.pdf', '2026-03-24 03:33:46'),
(20, 36, 'Certificate', '/uploads/mock_doc.pdf', '2026-03-24 03:33:46'),
(21, 36, 'Experience Letter', '/uploads/mock_doc.pdf', '2026-03-24 03:33:46'),
(22, 1, 'Skill Certificate', '/uploads/tech_doc_1_skill_certificate_1774304347.jpg', '2026-03-24 03:49:07'),
(23, 35, 'Government ID', '/uploads/tech_doc_35_government_id_1774304514.jpg', '2026-03-24 03:51:54');

-- --------------------------------------------------------

--
-- Table structure for table `technician_profiles`
--

CREATE TABLE `technician_profiles` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `skills` varchar(255) DEFAULT NULL,
  `experience` varchar(100) DEFAULT NULL,
  `service_radius` varchar(100) DEFAULT NULL,
  `working_hours` varchar(100) DEFAULT NULL,
  `verification_status` varchar(100) DEFAULT NULL,
  `payout_settings` varchar(100) DEFAULT NULL,
  `is_online` varchar(50) DEFAULT NULL,
  `rating` varchar(50) DEFAULT NULL,
  `profile_pic_url` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `technician_profiles`
--

INSERT INTO `technician_profiles` (`id`, `user_id`, `skills`, `experience`, `service_radius`, `working_hours`, `verification_status`, `payout_settings`, `is_online`, `rating`, `profile_pic_url`) VALUES
(5, 33, 'Electrician', '4', 'Current Range: 15 miles', '9:00 AM - 6:00 PM (Mon-Sat)', 'approved', 'Next Payout: Feb 20, 2026', 'true', '5.0', NULL),
(6, 35, 'electrician', '4 years', 'Current Range: 15 miles', '9:00 AM - 6:00 PM (Mon-Sat)', 'approved', 'Next Payout: Feb 20, 2026', 'true', '5.0', NULL),
(7, 36, 'plumber', '5 years', 'Current Range: 15 miles', '9:00 AM - 6:00 PM (Mon-Sat)', 'approved', 'Next Payout: Feb 20, 2026', 'true', '5.0', NULL);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `app_users`
--
ALTER TABLE `app_users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `bookings`
--
ALTER TABLE `bookings`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `customer_profiles`
--
ALTER TABLE `customer_profiles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_customer_profiles_user_id` (`user_id`),
  ADD KEY `ix_customer_profiles_id` (`id`);

--
-- Indexes for table `messages`
--
ALTER TABLE `messages`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `technician_documents`
--
ALTER TABLE `technician_documents`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_technician_documents_user_id` (`user_id`),
  ADD KEY `ix_technician_documents_id` (`id`);

--
-- Indexes for table `technician_profiles`
--
ALTER TABLE `technician_profiles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_technician_profiles_user_id` (`user_id`),
  ADD KEY `ix_technician_profiles_id` (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `app_users`
--
ALTER TABLE `app_users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=38;

--
-- AUTO_INCREMENT for table `bookings`
--
ALTER TABLE `bookings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=49;

--
-- AUTO_INCREMENT for table `customer_profiles`
--
ALTER TABLE `customer_profiles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `messages`
--
ALTER TABLE `messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=37;

--
-- AUTO_INCREMENT for table `technician_documents`
--
ALTER TABLE `technician_documents`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT for table `technician_profiles`
--
ALTER TABLE `technician_profiles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
